"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.CommonCstParser = exports.trimQuote = exports.parseVariableAsString = exports.parseVariableAsArray = exports.parseVariable = exports.getVariableRuleToken = void 0;
const chevrotain_1 = require("chevrotain");
const common_token_1 = require("./common-token");
const getVariableRuleToken = (variable) => {
    var _a, _b, _c, _d, _e;
    const childToken = (_d = (_b = (_a = variable.children.SUP_SGL_QUOTE_IDENTIFIER) === null || _a === void 0 ? void 0 : _a[0]) !== null && _b !== void 0 ? _b : (_c = variable.children.SUP_DBL_QUOTE_IDENTIFIER) === null || _c === void 0 ? void 0 : _c[0]) !== null && _d !== void 0 ? _d : (_e = variable.children.IDENTIFIER) === null || _e === void 0 ? void 0 : _e[0];
    return Object.assign(Object.assign({}, variable), { startOffset: childToken === null || childToken === void 0 ? void 0 : childToken.startOffset, endOffset: childToken === null || childToken === void 0 ? void 0 : childToken.endOffset, startLine: childToken === null || childToken === void 0 ? void 0 : childToken.startLine, endLine: childToken === null || childToken === void 0 ? void 0 : childToken.endLine, startColumn: childToken === null || childToken === void 0 ? void 0 : childToken.startColumn, endColumn: childToken === null || childToken === void 0 ? void 0 : childToken.endColumn });
};
exports.getVariableRuleToken = getVariableRuleToken;
const parseVariable = (variable) => {
    var _a, _b, _c, _d, _e, _f, _g, _h, _j, _k, _l, _m, _o, _p, _q, _r;
    if (Array.isArray(variable)) {
        if (variable.length === 1) {
            return (0, exports.parseVariable)(variable[0]);
        }
        return variable.map((eachVar) => (0, exports.parseVariable)(eachVar));
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
        return ((_p = (_l = (_k = (_j = variable.children.IDENTIFIER) === null || _j === void 0 ? void 0 : _j[0]) === null || _k === void 0 ? void 0 : _k.image) !== null && _l !== void 0 ? _l : (0, exports.trimQuote)((_o = (_m = variable.children.SUP_SGL_QUOTE_IDENTIFIER) === null || _m === void 0 ? void 0 : _m[0]) === null || _o === void 0 ? void 0 : _o.image)) !== null && _p !== void 0 ? _p : (0, exports.trimQuote)((_r = (_q = variable.children.SUP_DBL_QUOTE_IDENTIFIER) === null || _q === void 0 ? void 0 : _q[0]) === null || _r === void 0 ? void 0 : _r.image));
    }
};
exports.parseVariable = parseVariable;
const parseVariableAsArray = (variable) => {
    const result = (0, exports.parseVariable)(variable);
    if (!Array.isArray(result)) {
        return [result];
    }
    else {
        return result;
    }
};
exports.parseVariableAsArray = parseVariableAsArray;
const parseVariableAsString = (variable) => {
    const result = (0, exports.parseVariable)(variable);
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
exports.parseVariableAsString = parseVariableAsString;
const trimQuote = (value) => {
    if (value === undefined) {
        return value;
    }
    return value === null || value === void 0 ? void 0 : value.substring(1, value.length - 1);
};
exports.trimQuote = trimQuote;
class CommonCstParser extends chevrotain_1.CstParser {
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
                            $.CONSUME(common_token_1.COMMON_TOKEN.EMPTY_QUOTED_IDENTIFIER);
                        },
                    },
                    {
                        ALT: () => {
                            $.CONSUME(common_token_1.COMMON_TOKEN.SUP_SGL_QUOTE_IDENTIFIER);
                        },
                    },
                    {
                        ALT: () => {
                            $.CONSUME(common_token_1.COMMON_TOKEN.SUP_DBL_QUOTE_IDENTIFIER);
                        },
                    },
                    {
                        ALT: () => {
                            $.CONSUME(common_token_1.COMMON_TOKEN.COMMA_SUPPORTED_IDENTIFIER);
                        },
                    },
                    {
                        ALT: () => {
                            $.CONSUME(common_token_1.COMMON_TOKEN.IDENTIFIER);
                        },
                    },
                ]);
            });
        }
    }
}
exports.CommonCstParser = CommonCstParser;
//# sourceMappingURL=data:application/json;base64,eyJ2ZXJzaW9uIjozLCJmaWxlIjoiY29tbW9uLWNzdC1wYXJzZXIuanMiLCJzb3VyY2VSb290IjoiIiwic291cmNlcyI6WyIuLi8uLi8uLi8uLi9zcmMvbGliL3BhcnNlci9jb21tb24tY3N0LXBhcnNlci50cyJdLCJuYW1lcyI6W10sIm1hcHBpbmdzIjoiOzs7QUFBQSwyQ0FBa0Q7QUFDbEQsaURBQThDO0FBNEJ2QyxNQUFNLG9CQUFvQixHQUFHLENBQUMsUUFBc0IsRUFBRSxFQUFFOztJQUM3RCxNQUFNLFVBQVUsR0FDZCxNQUFBLE1BQUEsTUFBQSxRQUFRLENBQUMsUUFBUSxDQUFDLHdCQUF3QiwwQ0FBRyxDQUFDLENBQUMsbUNBQy9DLE1BQUEsUUFBUSxDQUFDLFFBQVEsQ0FBQyx3QkFBd0IsMENBQUcsQ0FBQyxDQUFDLG1DQUMvQyxNQUFBLFFBQVEsQ0FBQyxRQUFRLENBQUMsVUFBVSwwQ0FBRyxDQUFDLENBQUMsQ0FBQztJQUNwQyx1Q0FDSyxRQUFRLEtBQ1gsV0FBVyxFQUFFLFVBQVUsYUFBVixVQUFVLHVCQUFWLFVBQVUsQ0FBRSxXQUFXLEVBQ3BDLFNBQVMsRUFBRSxVQUFVLGFBQVYsVUFBVSx1QkFBVixVQUFVLENBQUUsU0FBUyxFQUNoQyxTQUFTLEVBQUUsVUFBVSxhQUFWLFVBQVUsdUJBQVYsVUFBVSxDQUFFLFNBQVMsRUFDaEMsT0FBTyxFQUFFLFVBQVUsYUFBVixVQUFVLHVCQUFWLFVBQVUsQ0FBRSxPQUFPLEVBQzVCLFdBQVcsRUFBRSxVQUFVLGFBQVYsVUFBVSx1QkFBVixVQUFVLENBQUUsV0FBVyxFQUNwQyxTQUFTLEVBQUUsVUFBVSxhQUFWLFVBQVUsdUJBQVYsVUFBVSxDQUFFLFNBQVMsSUFDaEM7QUFDSixDQUFDLENBQUM7QUFkVyxRQUFBLG9CQUFvQix3QkFjL0I7QUFFSyxNQUFNLGFBQWEsR0FBRyxDQUMzQixRQUF1QyxFQUNwQixFQUFFOztJQUNyQixJQUFJLEtBQUssQ0FBQyxPQUFPLENBQUMsUUFBUSxDQUFDLEVBQUUsQ0FBQztRQUM1QixJQUFJLFFBQVEsQ0FBQyxNQUFNLEtBQUssQ0FBQyxFQUFFLENBQUM7WUFDMUIsT0FBTyxJQUFBLHFCQUFhLEVBQUMsUUFBUSxDQUFDLENBQUMsQ0FBQyxDQUFDLENBQUM7UUFDcEMsQ0FBQztRQUNELE9BQU8sUUFBUSxDQUFDLEdBQUcsQ0FBQyxDQUFDLE9BQU8sRUFBRSxFQUFFLENBQUMsSUFBQSxxQkFBYSxFQUFDLE9BQU8sQ0FBVyxDQUFDLENBQUM7SUFDckUsQ0FBQztTQUFNLENBQUM7UUFDTixJQUNFLENBQUEsTUFBQSxNQUFBLFFBQVEsQ0FBQyxRQUFRLENBQUMsVUFBVSwwQ0FBRyxDQUFDLENBQUMsMENBQUUsS0FBSztZQUN4QyxDQUFDLENBQUEsTUFBQSxNQUFBLFFBQVEsQ0FBQyxRQUFRLENBQUMsVUFBVSwwQ0FBRyxDQUFDLENBQUMsMENBQUUsS0FBSyxNQUFLLE1BQU07Z0JBQ2xELENBQUEsTUFBQSxNQUFBLFFBQVEsQ0FBQyxRQUFRLENBQUMsVUFBVSwwQ0FBRyxDQUFDLENBQUMsMENBQUUsS0FBSyxNQUFLLE1BQU0sQ0FBQyxFQUN0RCxDQUFDO1lBQ0QsT0FBTyxJQUFJLENBQUM7UUFDZCxDQUFDO2FBQU0sSUFDTCxRQUFRLENBQUMsUUFBUSxDQUFDLHVCQUF1QjthQUN6QyxNQUFBLE1BQUEsUUFBUSxDQUFDLFFBQVEsQ0FBQyx1QkFBdUIsMENBQUcsQ0FBQyxDQUFDLDBDQUFFLEtBQUssQ0FBQSxFQUNyRCxDQUFDO1lBQ0QsT0FBTyxFQUFFLENBQUM7UUFDWixDQUFDO1FBQ0QsT0FBTyxDQUNMLE1BQUEsTUFBQSxNQUFBLE1BQUEsUUFBUSxDQUFDLFFBQVEsQ0FBQyxVQUFVLDBDQUFHLENBQUMsQ0FBQywwQ0FBRSxLQUFLLG1DQUN4QyxJQUFBLGlCQUFTLEVBQUMsTUFBQSxNQUFBLFFBQVEsQ0FBQyxRQUFRLENBQUMsd0JBQXdCLDBDQUFHLENBQUMsQ0FBQywwQ0FBRSxLQUFLLENBQUMsbUNBQ2pFLElBQUEsaUJBQVMsRUFBQyxNQUFBLE1BQUEsUUFBUSxDQUFDLFFBQVEsQ0FBQyx3QkFBd0IsMENBQUcsQ0FBQyxDQUFDLDBDQUFFLEtBQUssQ0FBQyxDQUNsRSxDQUFDO0lBQ0osQ0FBQztBQUNILENBQUMsQ0FBQztBQTNCVyxRQUFBLGFBQWEsaUJBMkJ4QjtBQUNLLE1BQU0sb0JBQW9CLEdBQUcsQ0FDbEMsUUFBdUMsRUFDN0IsRUFBRTtJQUNaLE1BQU0sTUFBTSxHQUFHLElBQUEscUJBQWEsRUFBQyxRQUFRLENBQUMsQ0FBQztJQUN2QyxJQUFJLENBQUMsS0FBSyxDQUFDLE9BQU8sQ0FBQyxNQUFNLENBQUMsRUFBRSxDQUFDO1FBQzNCLE9BQU8sQ0FBQyxNQUFNLENBQUMsQ0FBQztJQUNsQixDQUFDO1NBQU0sQ0FBQztRQUNOLE9BQU8sTUFBTSxDQUFDO0lBQ2hCLENBQUM7QUFDSCxDQUFDLENBQUM7QUFUVyxRQUFBLG9CQUFvQix3QkFTL0I7QUFFSyxNQUFNLHFCQUFxQixHQUFHLENBQ25DLFFBQXVDLEVBQ3ZDLEVBQUU7SUFDRixNQUFNLE1BQU0sR0FBRyxJQUFBLHFCQUFhLEVBQUMsUUFBUSxDQUFDLENBQUM7SUFDdkMsSUFBSSxLQUFLLENBQUMsT0FBTyxDQUFDLE1BQU0sQ0FBQyxFQUFFLENBQUM7UUFDMUIsSUFBSSxNQUFNLENBQUMsTUFBTSxDQUFDLENBQUMsQ0FBQyxFQUFFLEVBQUUsQ0FBQyxDQUFDLEtBQUssSUFBSSxDQUFDLENBQUMsTUFBTSxLQUFLLE1BQU0sQ0FBQyxNQUFNLEVBQUUsQ0FBQztZQUM5RCxPQUFPLElBQUksQ0FBQztRQUNkLENBQUM7YUFBTSxDQUFDO1lBQ04sT0FBTyxNQUFNLENBQUMsSUFBSSxDQUFDLEdBQUcsQ0FBQyxDQUFDO1FBQzFCLENBQUM7SUFDSCxDQUFDO1NBQU0sQ0FBQztRQUNOLE9BQU8sTUFBTSxDQUFDO0lBQ2hCLENBQUM7QUFDSCxDQUFDLENBQUM7QUFiVyxRQUFBLHFCQUFxQix5QkFhaEM7QUFFSyxNQUFNLFNBQVMsR0FBRyxDQUFDLEtBQWMsRUFBRSxFQUFFO0lBQzFDLElBQUksS0FBSyxLQUFLLFNBQVMsRUFBRSxDQUFDO1FBQ3hCLE9BQU8sS0FBSyxDQUFDO0lBQ2YsQ0FBQztJQUNELE9BQU8sS0FBSyxhQUFMLEtBQUssdUJBQUwsS0FBSyxDQUFFLFNBQVMsQ0FBQyxDQUFDLEVBQUUsS0FBSyxDQUFDLE1BQU0sR0FBRyxDQUFDLENBQUMsQ0FBQztBQUMvQyxDQUFDLENBQUM7QUFMVyxRQUFBLFNBQVMsYUFLcEI7QUFFRixNQUFzQixlQUFnQixTQUFRLHNCQUFTO0lBQ3JELFlBQ0UsTUFBbUIsRUFDbkIsTUFBc0I7UUFDcEIsWUFBWSxFQUFFO1lBQ1osUUFBUSxFQUFFLFVBQVU7U0FDckI7S0FDRjtRQUVELEtBQUssQ0FBQyxNQUFNLENBQUMsQ0FBQztRQUNkLElBQUksQ0FBQyxrQkFBa0IsQ0FBQyxHQUFHLENBQUMsQ0FBQztJQUMvQixDQUFDO0lBRVMsa0JBQWtCLENBQUMsR0FBbUI7UUFDOUMsTUFBTSxDQUFDLEdBQUcsSUFBSSxDQUFDO1FBQ2YsSUFBSSxHQUFHLENBQUMsWUFBWSxDQUFDLFFBQVEsRUFBRSxDQUFDO1lBQzlCLENBQUMsQ0FBQyxJQUFJLENBQUMsR0FBRyxDQUFDLFlBQVksQ0FBQyxRQUFRLEVBQUUsR0FBRyxFQUFFO2dCQUNyQyxDQUFDLENBQUMsRUFBRSxDQUFDO29CQUNIO3dCQUNFLEdBQUcsRUFBRSxHQUFHLEVBQUU7NEJBQ1IsQ0FBQyxDQUFDLE9BQU8sQ0FBQywyQkFBWSxDQUFDLHVCQUF1QixDQUFDLENBQUM7d0JBQ2xELENBQUM7cUJBQ0Y7b0JBQ0Q7d0JBQ0UsR0FBRyxFQUFFLEdBQUcsRUFBRTs0QkFDUixDQUFDLENBQUMsT0FBTyxDQUFDLDJCQUFZLENBQUMsd0JBQXdCLENBQUMsQ0FBQzt3QkFDbkQsQ0FBQztxQkFDRjtvQkFDRDt3QkFDRSxHQUFHLEVBQUUsR0FBRyxFQUFFOzRCQUNSLENBQUMsQ0FBQyxPQUFPLENBQUMsMkJBQVksQ0FBQyx3QkFBd0IsQ0FBQyxDQUFDO3dCQUNuRCxDQUFDO3FCQUNGO29CQUNEO3dCQUNFLEdBQUcsRUFBRSxHQUFHLEVBQUU7NEJBQ1IsQ0FBQyxDQUFDLE9BQU8sQ0FBQywyQkFBWSxDQUFDLDBCQUEwQixDQUFDLENBQUM7d0JBQ3JELENBQUM7cUJBQ0Y7b0JBQ0Q7d0JBQ0UsR0FBRyxFQUFFLEdBQUcsRUFBRTs0QkFDUixDQUFDLENBQUMsT0FBTyxDQUFDLDJCQUFZLENBQUMsVUFBVSxDQUFDLENBQUM7d0JBQ3JDLENBQUM7cUJBQ0Y7aUJBQ0YsQ0FBQyxDQUFDO1lBQ0wsQ0FBQyxDQUFDLENBQUM7UUFDTCxDQUFDO0lBQ0gsQ0FBQztDQUNGO0FBL0NELDBDQStDQyJ9