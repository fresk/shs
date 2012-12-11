#ifdef GL_ES
    precision highp float;
#endif

const vec3 LIGHT_COLOR = vec3(1,1,1);
const vec3 AMBIENT = vec3(0.2, 0.2, 0.2);

/* uniforms */
uniform sampler2D texture0;
uniform sampler2D texture1;

uniform mat4 modelview_mat;

/* Outputs from the vertex shader */
varying vec3 normal_vec;
varying vec4 frag_color;
varying vec2 tex_coord0;
varying vec3 eye_vec;
varying vec3 light_vec;





void main (void){
    vec3 diffuse = vec3(0.0, 0.0, 0.0);
    vec3 specular = vec3(0.0, 0.0, 0.0);



    vec3 v_normal = normalize(normal_vec);//
    //vec3 v_normal = normalize(texture2D(texture0, tex_coord0).xzy);
    mat4  nmat = transpose(inverse(modelview_mat));
    v_normal = normalize(vec3( nmat* vec4(v_normal.xyz, 0.0)));

    vec3 v_eye = normalize(eye_vec);
    vec3 v_light = normalize(light_vec);

    //diffuse light
    float diffuse_dot = dot(v_normal, v_light);
    diffuse += LIGHT_COLOR * clamp(diffuse_dot, 0.0, 1.0);

    //vec3 half_vec = dot(v_normal, normalize(v_eye + v_light));
    //float spec_color = min(LIGHT_COLOR +0.5, 1.0);
    //specular += spec_color * pow(clamp(half_vec, 0.0,1.0), 16.0);
    //vec4 col = frag_color;
    vec4 col = texture2D(texture1, tex_coord0) * frag_color;
    gl_FragColor = vec4(clamp(col.rgb * diffuse + AMBIENT, 0.0, 1.0), frag_color.a);
}

