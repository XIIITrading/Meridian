import { ColumnType, FilterType } from '../lib/Api';
import { FilterParseError, UITypes } from '../lib/index';
export { COMPARISON_OPS, COMPARISON_SUB_OPS, GROUPBY_COMPARISON_OPS, IS_WITHIN_COMPARISON_SUB_OPS, } from '../lib/parser/queryFilter/query-filter-lexer';
export declare function extractFilterFromXwhere(str: string | string[], aliasColObjMap: {
    [columnAlias: string]: ColumnType;
}, throwErrorIfInvalid?: boolean, errors?: FilterParseError[]): {
    filters?: FilterType[];
    errors?: FilterParseError[];
};
/**
 * Validates a filter comparison operation and its sub-operation.
 *
 * @param {UITypes} uidt - The UI type to validate against.
 * @param {any} op - The main comparison operator.
 * @param {any} [sub_op] - The optional sub-operation.
 * @param {FilterParseError[]} [errors=[]] - An optional array to collect errors.
 * @returns {FilterParseError[]} - An array of validation errors, empty if no errors.
 *
 * This function checks if the given `op` is a valid comparison operator and, if a `sub_op` is provided,
 * ensures it is compatible with the given `uidt`. If any validation fails, errors are added to the array
 * and returned instead of throwing an exception.
 */
export declare function validateFilterComparison(uidt: UITypes, op: any, sub_op?: any, errors?: FilterParseError[], validateFilterComparison?: boolean): FilterParseError[];
export declare function extractCondition(nestedArrayConditions: string[], aliasColObjMap: {
    [columnAlias: string]: ColumnType;
}, throwErrorIfInvalid: boolean, errors: FilterParseError[]): {
    filters?: FilterType[];
    errors?: FilterParseError[];
};
