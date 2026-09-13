grammar MiniCalc;

program
    : statement* EOF
    ;

statement
    : 'let' Identifier '=' IntegerLiteral ';'
    | 'print' Identifier ';'
    ;

Identifier
    : [a-zA-Z_] [a-zA-Z_0-9]*
    ;

IntegerLiteral
    : [0-9]+
    ;

Whitespace
    : [ \t\r\n]+ -> skip
    ;
