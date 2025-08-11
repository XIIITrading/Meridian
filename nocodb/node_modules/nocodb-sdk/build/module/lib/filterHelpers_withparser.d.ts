import { ColumnType, FilterType } from '../lib/Api';
import { FilterParseError } from './filterHelpers';
export { COMPARISON_OPS, COMPARISON_SUB_OPS, GROUPBY_COMPARISON_OPS, IS_WITHIN_COMPARISON_SUB_OPS, } from '../lib/parser/queryFilter/query-filter-lexer';
export declare function extractFilterFromXwhere(str: string | string[], aliasColObjMap: {
    [columnAlias: string]: ColumnType;
}, throwErrorIfInvalid?: boolean, errors?: FilterParseError[]): {
    filters?: FilterType[];
    errors?: FilterParseError[];
};
