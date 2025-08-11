import { CstParser } from 'chevrotain';
import { COMMON_TOKEN } from './common-token';
export const getVariableRuleToken = (variable) => {
    var _a, _b, _c, _d, _e;
    const childToken = (_d = (_b = (_a = variable.children.SUP_SGL_QUOTE_IDENTIFIER) === null || _a === void 0 ? void 0 : _a[0]) !== null && _b !== void 0 ? _b : (_c = variable.children.SUP_DBL_QUOTE_IDENTIFIER) === null || _c === void 0 ? void 0 : _c[0]) !== null && _d !== void 0 ? _d : (_e = variable.children.IDENTIFIER) === null || _e === void 0 ? void 0 : _e[0];
    return Object.assign(Object.assign({}, variable), { startOffset: childToken === null || childToken === void 0 ? void 0 : childToken.startOffset, endOffset: childToken === null || childToken === void 0 ? void 0 : childToken.endOffset, startLine: childToken === null || childToken === void 0 ? void 0 : childToken.startLine, endLine: childToken === null || childToken === void 0 ? void 0 : childToken.endLine, startColumn: childToken === null || childToken === void 0 ? void 0 : childToken.startColumn, endColumn: childToken === null || childToken === void 0 ? void 0 : childToken.endColumn });
};
export const parseVariable = (variable) => {
    var _a, _b, _c, _d, _e, _f, _g, _h, _j, _k, _l, _m, _o, _p, _q, _r;
    if (Array.isArray(variable)) {
        if (variable.length === 1) {
            return parseVariable(variable[0]);
        }
        return variable.map((eachVar) => parseVariable(eachVar));
    }
    else {
        if (((_b = (_a = variable.children.IDENTIFIER) === null || _a === void 0 ? void 0 : _a[0]) === null || _b === void 0 ? void 0 : _b.image) &&
            (((_d = (_c = variable.children.IDENTIFIER) === null || _c === void 0 ? void 0 : _c[0]) === null || _d === void 0 ? void 0 : _d.image) === 'NULL' ||
                ((_f = (_e = variable.children.IDENTIFIER) === null || _e === void 0 ? void 0 : _e[0]) === null || _f === void 0 ? void 0 : _f.image) === 'null')) {
            return null;
        }
        else if (variable.children.EMPTY_QUOTED_IDENTIFIER &&
            ((_h = (_g = variable.children.EMPTY_QUOTED_IDENTIFIER) === null || _g === void 0 ? void 0 : _g[0]) === null || _h === void 0 ? void 0 : _h.image)) {
            return '';
        }
        return ((_p = (_l = (_k = (_j = variable.children.IDENTIFIER) === null || _j === void 0 ? void 0 : _j[0]) === null || _k === void 0 ? void 0 : _k.image) !== null && _l !== void 0 ? _l : trimQuote((_o = (_m = variable.children.SUP_SGL_QUOTE_IDENTIFIER) === null || _m === void 0 ? void 0 : _m[0]) === null || _o === void 0 ? void 0 : _o.image)) !== null && _p !== void 0 ? _p : trimQuote((_r = (_q = variable.children.SUP_DBL_QUOTE_IDENTIFIER) === null || _q === void 0 ? void 0 : _q[0]) === null || _r === void 0 ? void 0 : _r.image));
    }
};
export const parseVariableAsArray = (variable) => {
    const result = parseVariable(variable);
    if (!Array.isArray(result)) {
        return [result];
    }
    else {
        return result;
    }
};
export const parseVariableAsString = (variable) => {
    const result = parseVariable(variable);
    if (Array.isArray(result)) {
        if (result.filter((k) => k === null).length === result.length) {
            return null;
        }
        else {
            return result.join(' ');
        }
    }
    else {
        return result;
    }
};
export const trimQuote = (value) => {
    if (value === undefined) {
        return value;
    }
    return value === null || value === void 0 ? void 0 : value.substring(1, value.length - 1);
};
export class CommonCstParser extends CstParser {
    constructor(tokens, opt = {
        enabledRules: {
            VARIABLE: 'VARIABLE',
        },
    }) {
        super(tokens);
        this.prepareCommonRules(opt);
    }
    prepareCommonRules(opt) {
        const $ = this;
        if (opt.enabledRules.VARIABLE) {
            $.RULE(opt.enabledRules.VARIABLE, () => {
                $.OR([
                    {
                        ALT: () => {
                            $.CONSUME(COMMON_TOKEN.EMPTY_QUOTED_IDENTIFIER);
                        },
                    },
                    {
                        ALT: () => {
                            $.CONSUME(COMMON_TOKEN.SUP_SGL_QUOTE_IDENTIFIER);
                        },
                    },
                    {
                        ALT: () => {
                            $.CONSUME(COMMON_TOKEN.SUP_DBL_QUOTE_IDENTIFIER);
                        },
                    },
                    {
                        ALT: () => {
                            $.CONSUME(COMMON_TOKEN.COMMA_SUPPORTED_IDENTIFIER);
                        },
                    },
                    {
                        ALT: () => {
                            $.CONSUME(COMMON_TOKEN.IDENTIFIER);
                        },
                    },
                ]);
            });
        }
    }
}
//# sourceMappingURL=data:application/json;base64,eyJ2ZXJzaW9uIjozLCJmaWxlIjoiY29tbW9uLWNzdC1wYXJzZXIuanMiLCJzb3VyY2VSb290IjoiIiwic291cmNlcyI6WyIuLi8uLi8uLi8uLi9zcmMvbGliL3BhcnNlci9jb21tb24tY3N0LXBhcnNlci50cyJdLCJuYW1lcyI6W10sIm1hcHBpbmdzIjoiQUFBQSxPQUFPLEVBQUUsU0FBUyxFQUFhLE1BQU0sWUFBWSxDQUFDO0FBQ2xELE9BQU8sRUFBRSxZQUFZLEVBQUUsTUFBTSxnQkFBZ0IsQ0FBQztBQTRCOUMsTUFBTSxDQUFDLE1BQU0sb0JBQW9CLEdBQUcsQ0FBQyxRQUFzQixFQUFFLEVBQUU7O0lBQzdELE1BQU0sVUFBVSxHQUNkLE1BQUEsTUFBQSxNQUFBLFFBQVEsQ0FBQyxRQUFRLENBQUMsd0JBQXdCLDBDQUFHLENBQUMsQ0FBQyxtQ0FDL0MsTUFBQSxRQUFRLENBQUMsUUFBUSxDQUFDLHdCQUF3QiwwQ0FBRyxDQUFDLENBQUMsbUNBQy9DLE1BQUEsUUFBUSxDQUFDLFFBQVEsQ0FBQyxVQUFVLDBDQUFHLENBQUMsQ0FBQyxDQUFDO0lBQ3BDLHVDQUNLLFFBQVEsS0FDWCxXQUFXLEVBQUUsVUFBVSxhQUFWLFVBQVUsdUJBQVYsVUFBVSxDQUFFLFdBQVcsRUFDcEMsU0FBUyxFQUFFLFVBQVUsYUFBVixVQUFVLHVCQUFWLFVBQVUsQ0FBRSxTQUFTLEVBQ2hDLFNBQVMsRUFBRSxVQUFVLGFBQVYsVUFBVSx1QkFBVixVQUFVLENBQUUsU0FBUyxFQUNoQyxPQUFPLEVBQUUsVUFBVSxhQUFWLFVBQVUsdUJBQVYsVUFBVSxDQUFFLE9BQU8sRUFDNUIsV0FBVyxFQUFFLFVBQVUsYUFBVixVQUFVLHVCQUFWLFVBQVUsQ0FBRSxXQUFXLEVBQ3BDLFNBQVMsRUFBRSxVQUFVLGFBQVYsVUFBVSx1QkFBVixVQUFVLENBQUUsU0FBUyxJQUNoQztBQUNKLENBQUMsQ0FBQztBQUVGLE1BQU0sQ0FBQyxNQUFNLGFBQWEsR0FBRyxDQUMzQixRQUF1QyxFQUNwQixFQUFFOztJQUNyQixJQUFJLEtBQUssQ0FBQyxP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