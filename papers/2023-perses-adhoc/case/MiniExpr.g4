grammar MiniExpr;

program
    : dropStatement? dropStatement? keepStatement dropStatement? dropStatement? EOF
    ;

dropStatement
    : DROP Identifier SEMI
    ;

keepStatement
    : KEEP Identifier SEMI
    ;

KEEP: 'keep';
DROP: 'drop';
SEMI: ';';
Identifier: [a-zA-Z_] [a-zA-Z_0-9]*;
WS: [ \t\r\n]+ -> skip;
