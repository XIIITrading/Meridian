import { VariableRule } from '../common-cst-parser';
import type { Rule, Token } from '../common-type';
export interface CstExpressionArguments extends Rule<{
    VARIABLE: VariableRule[];
    COMMA: Token[];
}, 'expression_arguments'> {
}
export interface CstMultiClause extends Rule<{
    clause: (CstAndOrClause | CstNotClause | CstParenClause)[];
}, 'multi_clause'> {
}
export interface CstAndOrClause extends Rule<{
    clause: CstParenClause[];
    operator: Token[];
}, 'and_or_clause'> {
}
export interface CstNotClause extends Rule<{
    clause: CstParenClause[];
}, 'not_clause'> {
}
export interface CstParenClause extends Rule<{
    clause: (CstMultiClause | CstCallExpression)[];
    PAREN_START: Token[];
    PAREN_END: Token[];
}, 'paren_clause'> {
}
export interface CstCallExpression extends Rule<{
    PAREN_START: Token[];
    VARIABLE: VariableRule[];
    COMMA: Token[];
    OPERATOR: Token[];
    expression_arguments: CstExpressionArguments[];
    PAREN_END: Token[];
}, 'call_expression'> {
}
export interface FilterClauseSubType {
    is_group: false;
    field: string;
    logical_op?: string;
    comparison_op: string;
    comparison_sub_op?: string;
    value?: string | string[];
}
export interface FilterGroupSubType {
    is_group: true;
    logical_op: string;
    children?: FilterSubtype;
}
export type FilterSubtype = (FilterClauseSubType | FilterGroupSubType)[];
export declare const parseExpressionArguments: (cst: CstExpressionArguments) => string[];
export declare const parseMultiClause: (cst: CstMultiClause, opt?: {
    logicalOperator?: string;
}) => FilterGroupSubType;
export declare const parseNotClause: (cst: CstNotClause) => FilterClauseSubType | FilterGroupSubType;
export declare const parseAndOrClause: (cst: CstAndOrClause) => FilterClauseSubType | FilterGroupSubType;
export declare const parseParenClause: (cst: CstParenClause, opt?: {
    logicalOperator?: string;
}) => FilterClauseSubType | FilterGroupSubType;
export declare const parseCallExpression: (cst: CstCallExpression, opt?: {
    logicalOperator?: string;
}) => FilterClauseSubType;
export declare const parseCst: (cst: CstMultiClause) => FilterGroupSubType;
