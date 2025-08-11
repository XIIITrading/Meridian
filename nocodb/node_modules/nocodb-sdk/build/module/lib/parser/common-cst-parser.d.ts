import { CstParser, TokenType } from 'chevrotain';
import { Rule, Token } from './common-type';
type ConstructorOpt = {
    enabledRules: {
        VARIABLE?: string | null;
        SGL_QUOTE_IDENTIFIER?: string | null;
        DBL_QUOTE_IDENTIFIER?: string | null;
    };
};
export type VariableRule = Rule<{
    IDENTIFIER?: Token[];
    SUP_SGL_QUOTE_IDENTIFIER?: Token[];
    SUP_DBL_QUOTE_IDENTIFIER?: Token[];
    EMPTY_QUOTED_IDENTIFIER?: Token[];
}, 'VARIABLE'>;
export type VariableRuleToken = VariableRule & {
    startOffset: number;
    endOffset: number;
    startLine: number;
    endLine: number;
    startColumn: number;
    endColumn: number;
};
export declare const getVariableRuleToken: (variable: VariableRule) => {
    startOffset: number;
    endOffset: number;
    startLine: number;
    endLine: number;
    startColumn: number;
    endColumn: number;
    name: "VARIABLE";
    children: {
        IDENTIFIER?: Token[];
        SUP_SGL_QUOTE_IDENTIFIER?: Token[];
        SUP_DBL_QUOTE_IDENTIFIER?: Token[];
        EMPTY_QUOTED_IDENTIFIER?: Token[];
    };
};
export declare const parseVariable: (variable: VariableRule | VariableRule[]) => string | string[];
export declare const parseVariableAsArray: (variable: VariableRule | VariableRule[]) => string[];
export declare const parseVariableAsString: (variable: VariableRule | VariableRule[]) => string;
export declare const trimQuote: (value?: string) => string;
export declare abstract class CommonCstParser extends CstParser {
    constructor(tokens: TokenType[], opt?: ConstructorOpt);
    protected prepareCommonRules(opt: ConstructorOpt): void;
}
export {};
