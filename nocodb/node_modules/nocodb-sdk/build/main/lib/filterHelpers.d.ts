import { ColumnType, FilterType } from '../lib/Api';
export { COMPARISON_OPS, COMPARISON_SUB_OPS, GROUPBY_COMPARISON_OPS, IS_WITHIN_COMPARISON_SUB_OPS, } from '../lib/parser/queryFilter/query-filter-lexer';
import { NcContext } from './ncTypes';
export interface FilterParseError {
    message: string;
}
/**
 * Converts a flat array of filter objects into a nested tree structure
 * @param {FilterType[]} items - Array of filter objects
 * @returns {FilterType[]} - Nested tree structure
 */
export declare function buildFilterTree(items: FilterType[]): FilterType[];
export declare function extractFilterFromXwhere(context: Pick<NcContext, 'api_version'>, str: string | string[], aliasColObjMap: {
    [columnAlias: string]: ColumnType;
}, throwErrorIfInvalid?: boolean, errors?: FilterParseError[]): {
    filters?: FilterType[];
    errors?: FilterParseError[];
};
