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


void main (void) {
    vec4 position = modelview_mat * vec4(v_pos,1.0);
    frag_color = color;
    gl_Position = projection_mat * position;
}
