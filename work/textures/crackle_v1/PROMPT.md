# Crackle atlas source

Generated with the built-in image_gen tool. Source: `generated_atlas.png`.

Prompt: Create a production game VFX sprite atlas, square 1024x1024 RGBA transparent background. EXACT 4 by 4 equal grid, 16 cells, each cell 256x256. No drawn grid lines, no text, no labels. Each cell has one distinct narrow jagged branching electrical bolt running roughly horizontally from x=24 to x=232 at middle y=128 of its own cell, with 24 pixel clear transparent padding on every cell edge. Every frame is a different sudden branching bolt shape, NOT a smoothly undulating ribbon or wave. Sharp angular kinks, thin forked sparks, tiny broken satellite sparks. Brilliant near-white hot cores, narrow cobalt/dark navy-blue outer glow, little cyan. A few dimmer frames for irregular crackling flicker. Consistent framing/scale per cell. Flat orthographic particle textures only: no objects, no shield, no scenery, no shadows, no background checkerboard. Cells must not touch one another. Designed for a hard-cut looping 16-frame animation, not smooth scrolling.

Engine preparation rescales each cell into a padded 256px tile, retaining generated RGBA/alpha through resampling. No generated file is used outside the project.
