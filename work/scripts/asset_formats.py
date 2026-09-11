"""Independent binary readers and numerical validation for the supplied SKN/SKL."""
from pathlib import Path
import struct
import math
from collections import Counter

def read_skl(path):
    data = Path(path).read_bytes()
    assert struct.unpack_from('<II', data, 4) == (0x22FD4FC3, 0)
    count, palette_count, offset, _, palette_offset = struct.unpack_from('<HIiii', data, 14)
    joints = []
    for i in range(count):
        at = offset + i * 100
        name_at = at + 96 + struct.unpack_from('<i', data, at + 96)[0]
        name = data[name_at:data.index(b'\0', name_at)].decode('ascii')
        flags, idx, parent, other, hash_, radius = struct.unpack_from('<HHhHIf', data, at)
        joints.append(dict(name=name, id=idx, parent=parent, hash=hash_, flags=flags,
                           other_flags=other, radius=radius,
                           bind=struct.unpack_from('<10f', data, at + 16),
                           inverse_bind=struct.unpack_from('<10f', data, at + 56)))
    palette = struct.unpack_from(f'<{palette_count}H', data, palette_offset)
    assert len(set(j['name'] for j in joints)) == count
    assert all(-1 <= j['parent'] < count for j in joints)
    assert all(i < count for i in palette)
    return dict(joints=joints, palette=palette)

def read_skn(path):
    data = Path(path).read_bytes()
    magic, major, minor, count = struct.unpack_from('<IHHI', data)
    assert magic == 0x112233 and major in (1, 2, 4)
    offset = 12
    submeshes = []
    for _ in range(count):
        name = data[offset:offset+64].split(b'\0')[0].decode('ascii')
        vs, vc, start, size = struct.unpack_from('<4I', data, offset + 64)
        submeshes.append(dict(name=name, vertex_start=vs, vertex_count=vc, index_start=start, index_count=size))
        offset += 80
    if major == 4:
        offset += 4
    index_count, vertex_count = struct.unpack_from('<II', data, offset)
    offset += 8
    stride = 52
    if major == 4:
        stride = struct.unpack_from('<I', data, offset)[0]
        offset += 48
    indices = struct.unpack_from(f'<{index_count}H', data, offset)
    offset += index_count * 2
    vertices = []
    for i in range(vertex_count):
        v = struct.unpack_from('<3f4B4f3f2f', data, offset + i * stride)
        vertices.append(dict(position=v[:3], indices=v[3:7], weights=v[7:11], normal=v[11:14], uv=v[14:16]))
    assert index_count % 3 == 0 and max(indices) < vertex_count
    for s in submeshes:
        assert s['vertex_start'] + s['vertex_count'] <= vertex_count
        assert s['index_start'] + s['index_count'] <= index_count
        assert s['index_count'] % 3 == 0
        assert all(s['vertex_start'] <= i < s['vertex_start'] + s['vertex_count']
                   for i in indices[s['index_start']:s['index_start']+s['index_count']])
    return dict(version=[major, minor], submeshes=submeshes, vertices=vertices, indices=indices)

def joint_weights(vertex, skeleton):
    result = Counter()
    for i, w in zip(vertex['indices'], vertex['weights']):
        if w > 0:
            assert i < len(skeleton['palette'])
            result[skeleton['palette'][i]] += w
    return result

def validate_pair(mesh, skeleton):
    vertices = mesh['vertices']
    assert len(vertices) <= 65535
    assert len(skeleton['palette']) <= 256
    for v in vertices:
        assert all(math.isfinite(x) for key in ('position', 'weights', 'normal', 'uv') for x in v[key])
        assert all(w >= 0 for w in v['weights'])
        joint_weights(v, skeleton)
    error = max(abs(sum(v['weights']) - 1) for v in vertices)
    assert error < 1e-5, error
    return dict(vertices=len(vertices), triangles=len(mesh['indices'])//3,
                joints=len(skeleton['joints']), palette=len(skeleton['palette']),
                submeshes=mesh['submeshes'], max_weight_sum_error=error,
                bounds=[[min(v['position'][a] for v in vertices), max(v['position'][a] for v in vertices)] for a in range(3)])

def compare_roundtrip(source_mesh, source_skl, result_mesh, result_skl):
    assert len(source_skl['joints']) == len(result_skl['joints'])
    metadata_changes = []
    max_bind_error = 0
    for a, b in zip(source_skl['joints'], result_skl['joints']):
        for key in ('name', 'id', 'parent', 'hash'):
            assert a[key] == b[key], (key, a, b)
        for key in ('flags', 'other_flags', 'radius'):
            if a[key] != b[key]:
                metadata_changes.append(dict(joint=a['name'], field=key, before=a[key], after=b[key]))
        # Quaternion q and -q represent the same rotation.
        for key in ('bind', 'inverse_bind'):
            err = max(abs(x-y) for x,y in zip(a[key][:6], b[key][:6]))
            qerr = min(max(abs(x-y) for x,y in zip(a[key][6:],b[key][6:])),
                       max(abs(x+y) for x,y in zip(a[key][6:],b[key][6:])))
            max_bind_error = max(max_bind_error, err, qerr)
    assert max_bind_error < 0.001, max_bind_error
    # Exporter can reorder/split vertices; compare ordered triangle corners.
    assert [s['name'] for s in source_mesh['submeshes']] == [s['name'] for s in result_mesh['submeshes']]
    assert len(source_mesh['indices']) == len(result_mesh['indices'])
    errors = dict(position=0, uv=0, weight=0, normal=0)
    for ai, bi in zip(source_mesh['indices'], result_mesh['indices']):
        a, b = source_mesh['vertices'][ai], result_mesh['vertices'][bi]
        for key in ('position', 'uv', 'normal'):
            errors[key] = max(errors[key], max(abs(x-y) for x,y in zip(a[key],b[key])))
        wa, wb = joint_weights(a, source_skl), joint_weights(b, result_skl)
        errors['weight'] = max(errors['weight'], max(abs(wa[k]-wb[k]) for k in wa.keys() | wb.keys()))
    assert errors['position'] < 0.0001 and errors['uv'] < 1e-6 and errors['weight'] < 0.0002, errors
    return dict(max_bind_component_error=max_bind_error, max_corner_errors=errors,
                skeleton_metadata_changes=metadata_changes,
                palette_changed=source_skl['palette'] != result_skl['palette'])
