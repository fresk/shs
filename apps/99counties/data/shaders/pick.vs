#ifdef GL_ES
    precision highp float;
#endif

/* Outputs to the fragment shader */
varying vec4 frag_color;

/* vertex attributes */
attribute vec3     v_pos;
attribute vec3     v_normal;
attribute vec2     v_tc0;

/* uniform variables */
uniform mat4       modelview_mat;
uniform mat4       projection_mat;
uniform vec4       color;
uniform float      opacity;
uniform float      selection_id;



float packColor(vec3 color) {
    return color.r + color.g * 256.0 + color.b * 256.0 * 256.0;
}

vec3 unpackColor(float f) {
    vec3 color;
    color.b = floor(f / 256.0 / 256.0);
    color.g = floor((f - color.b * 256.0 * 256.0) / 256.0);
    color.r = floor(f - color.b * 256.0 * 256.0 - color.g * 256.0);
    // now we have a vec3 with the 3 components in range [0..256]. Let's normalize it!
    return color / 256.0;
}


void main (void) {
    vec4 position = modelview_mat * vec4(v_pos,1.0);
    vec3 pick_color = unpackColor(selection_id);
    frag_color = vec4(pick_color.rgb, 1.0);
    gl_Position = projection_mat * position;
}
