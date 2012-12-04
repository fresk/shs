#ifdef GL_ES
    precision highp float;
#endif

/* Outputs to the fragment shader */
varying vec4 frag_color;
varying vec2 tex_coord0;
varying vec3 normal_vec;
varying vec3 eye_vec;
varying vec3 light_vec;

/* vertex attributes */
attribute vec3     v_pos;
attribute vec3     v_normal;
attribute vec2     v_tc0;

/* uniform variables */
uniform mat4       modelview_mat;
uniform mat4       projection_mat;
uniform mat4       normal_mat;
uniform vec3       light_pos;
uniform vec4       color;
uniform float      opacity;


void main (void) {
  
    // set the normal for the fragment shader and
    // the vector from the vertex to the camera
    vec4 position = modelview_mat * vec4(v_pos,1.0);
    eye_vec = vec3(0,0,0) -  position.xyz;
    light_vec = vec3(0,1,0);
    normal_vec = v_normal; //vec3(modelview_mat * vec4(v_normal.xyz, 0.0));
    frag_color = color * vec4(.5,.5,.5, opacity);
    tex_coord0 = vec2(v_pos.x, 1.0-v_pos.y);
    gl_Position = projection_mat * position;
}
