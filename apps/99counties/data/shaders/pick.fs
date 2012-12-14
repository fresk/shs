#ifdef GL_ES
    precision highp float;
#endif
varying vec4 frag_color;
void main (void){
    if ( frag_color == vec4(0,0,0,0))
        discard;
    gl_FragColor = frag_color;
}

