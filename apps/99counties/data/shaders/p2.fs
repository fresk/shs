#ifdef GL_ES
    precision highp float;
#endif

const vec3 LIGHT_COLOR = vec3(1,1,1);
const vec3 AMBIENT = vec3(0.2, 0.2, 0.2);

/* uniforms */
uniform sampler2D texture0;
uniform sampler2D texture1;

uniform mat4 modelview_mat;
uniform mat4 normal_mat;

/* Outputs from the vertex shader */
varying vec4 normal_vec;
varying vec4 frag_color;
varying vec2 tex_coord0;
varying vec4 light_vec;


void main (void){
    vec4 v_normal;
    vec3 diffuse;
    vec4 col;
    float diffuse_dot;

    v_normal = normalize( normal_mat * normalize(normal_vec) );

    //diffuse light
    diffuse_dot = dot(v_normal, light_vec);
    diffuse = LIGHT_COLOR * clamp(diffuse_dot, 0.0, 1.0);

    col = frag_color;
    gl_FragColor = vec4(clamp(col.rgb * diffuse + AMBIENT, 0.0, 1.0), col.a);
}

