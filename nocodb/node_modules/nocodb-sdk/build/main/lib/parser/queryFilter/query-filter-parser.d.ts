import { CommonCstParser } from '../common-cst-parser';
export declare class QueryFilterParser extends CommonCstParser {
    constructor();
    private initializeRule;
    parse(): any;
    static parse(text: string): {
        cst: any;
        lexErrors: import("chevrotain").ILexingError[];
        parseErrors: import("chevrotain").IRecognitionException[];
        parsedCst: import("./query-filter-cst-parser").FilterGroupSubType;
    };
}
