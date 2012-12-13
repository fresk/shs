#ifdef GL_ES
    precision highp float;
#endif
/* vertex attributes */
attribute vec3     v_pos;
attribute vec3     v_normal;
attribute vec2     v_tc0;

/* uniform variables */
uniform mat4       modelview_mat;
uniform mat4       normal_mat;
uniform mat4       projection_mat;
uniform vec3       light_pos;
uniform vec4       color;
uniform float      opacity;


/* Outputs to the fragment shader */
varying vec4 frag_color;
varying vec4 normal_vec;
varying vec2 tex_coord0;
varying vec3 eye_vec;
varying vec4 light_vec;


void main (void) {
    vec4 position = modelview_mat * vec4(v_pos,1.0);
    normal_vec = normalize(vec4(v_normal, 0.0));
    frag_color = color * vec4(1.,1.,1., opacity);
    tex_coord0 = vec2(v_pos.x, 1.0-v_pos.y);
    light_vec = vec4(0.,0.,0.,1.) - position;
    gl_Position = projection_mat * position;
}
