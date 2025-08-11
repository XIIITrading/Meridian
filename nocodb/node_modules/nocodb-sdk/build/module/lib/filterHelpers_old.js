import { BadRequest, NcSDKError } from '../lib/errorUtils';
import { COMPARISON_OPS, COMPARISON_SUB_OPS, GROUPBY_COMPARISON_OPS, IS_WITHIN_COMPARISON_SUB_OPS, UITypes, } from '../lib/index';
export { COMPARISON_OPS, COMPARISON_SUB_OPS, GROUPBY_COMPARISON_OPS, IS_WITHIN_COMPARISON_SUB_OPS, } from '../lib/parser/queryFilter/query-filter-lexer';
export function extractFilterFromXwhere(str, aliasColObjMap, throwErrorIfInvalid = false, errors = []) {
    if (!str) {
        return { filters: [] };
    }
    // if array treat it as `and` group
    if (Array.isArray(str)) {
        const nestedFilters = str.map((s) => extractFilterFromXwhere(s, aliasColObjMap, throwErrorIfInvalid, errors));
        const filters = nestedFilters.reduce((acc, { filters }) => {
            if (!filters)
                return acc;
            return [...acc, ...filters];
        }, []);
        const collectedErrors = nestedFilters.reduce((acc, { errors }) => {
            if (!errors)
                return acc;
            return [...acc, ...errors];
        }, []);
        // If errors exist, return them
        if (collectedErrors.length > 0) {
            return { errors: collectedErrors };
        }
        // If there's only one filter, return it directly
        if (filters.length === 1) {
            return { filters };
        }
        // If there's only one filter, return it directly; otherwise, wrap in an AND group
        return {
            filters: [
                {
                    is_group: true,
                    logical_op: 'and',
                    children: filters,
                },
            ],
        };
    }
    // Validate input type
    if (typeof str !== 'string') {
        const error = {
            message: 'Invalid filter format. Expected string or array of strings.',
        };
        if (throwErrorIfInvalid)
            throw new Error(error.message);
        errors.push(error);
        return { errors };
    }
    let openIndex = str.indexOf('((');
    if (openIndex === -1)
        openIndex = str.indexOf('(~');
    // If it's a simple query, extract conditions directly
    if (openIndex === -1) {
        if (str !== '~not') {
            const nestedArrayConditions = str.split(/(?=~(?:or(?:not)?|and(?:not)?|not)\()/);
            return extractCondition(nestedArrayConditions, aliasColObjMap, throwErrorIfInvalid, errors);
        }
        return { filters: [] };
    }
    let closingIndex = str.indexOf('))');
    let nextOpenIndex = openIndex;
    // Iterate until the correct closing bracket is found
    while ((nextOpenIndex = str
        .substring(0, closingIndex)
        .indexOf('((', nextOpenIndex + 1)) !== -1) {
        closingIndex = str.indexOf('))', closingIndex + 1);
    }
    // If no closing bracket is found, return an error
    if (closingIndex === -1) {
        const error = {
            message: `${str
                .substring(0, openIndex + 1)
                .slice(-10)} : Closing bracket not found`,
        };
        if (throwErrorIfInvalid)
            throw new Error(error.message);
        errors.push(error);
        return { errors };
    }
    // Extract operator and left-hand side of nested query
    const operandStartIndex = str.lastIndexOf('~', openIndex);
    const operator = operandStartIndex !== -1
        ? str.substring(operandStartIndex + 1, openIndex)
        : '';
    const lhsOfNestedQuery = str.substring(0, openIndex);
    // Recursively process left-hand side, nested query, and right-hand side
    const lhsResult = extractFilterFromXwhere(lhsOfNestedQuery, aliasColObjMap, throwErrorIfInvalid, errors);
    const nestedQueryResult = extractFilterFromXwhere(str.substring(openIndex + 1, closingIndex + 1), aliasColObjMap, throwErrorIfInvalid, errors);
    const rhsResult = extractFilterFromXwhere(str.substring(closingIndex + 2), aliasColObjMap, throwErrorIfInvalid, errors);
    // If any errors occurred during recursion, return them
    if (lhsResult.errors || nestedQueryResult.errors || rhsResult.errors) {
        return {
            errors: [
                ...(lhsResult.errors || []),
                ...(nestedQueryResult.errors || []),
                ...(rhsResult.errors || []),
            ],
        };
    }
    // Return the combined filters
    return {
        filters: [
            ...(lhsResult.filters || []),
            {
                is_group: true,
                logical_op: operator,
                children: nestedQueryResult.filters || [],
            },
            ...(rhsResult.filters || []),
        ],
    };
}
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
export function validateFilterComparison(uidt, op, sub_op, errors = [], validateFilterComparison = false) {
    // Check if the main comparison operator is valid
    if (!COMPARISON_OPS.includes(op) && !GROUPBY_COMPARISON_OPS.includes(op)) {
        if (validateFilterComparison) {
            throw new BadRequest(`${op} is not supported.`);
        }
        errors.push({ message: `${op} is not supported.` });
    }
    if (sub_op) {
        // Ensure that sub-operators are only used with specific UI types
        if (![
            UITypes.Date,
            UITypes.DateTime,
            UITypes.CreatedTime,
            UITypes.LastModifiedTime,
        ].includes(uidt)) {
            if (validateFilterComparison) {
                throw new BadRequest(`'${sub_op}' is not supported for UI Type'${uidt}'.`);
            }
            errors.push({
                message: `'${sub_op}' is not supported for UI Type '${uidt}'.`,
            });
        }
        // Validate if the sub-operator exists in the allowed set
        if (!COMPARISON_SUB_OPS.includes(sub_op)) {
            if (validateFilterComparison) {
                throw new BadRequest(`'${sub_op}' is not supported.`);
            }
            errors.push({ message: `'${sub_op}' is not supported.` });
        }
        // Ensure `isWithin` has correct sub-operators, and other operators don't use `isWithin` sub-operators
        if ((op === 'isWithin' && !IS_WITHIN_COMPARISON_SUB_OPS.includes(sub_op)) ||
            (op !== 'isWithin' && IS_WITHIN_COMPARISON_SUB_OPS.includes(sub_op))) {
            if (validateFilterComparison) {
                throw new BadRequest(`'${sub_op}' is not supported for '${op}'`);
            }
            errors.push({ message: `'${sub_op}' is not supported for '${op}'.` });
        }
    }
    // Return collected errors, if any
    return errors.length > 0 ? errors : [];
}
export function extractCondition(nestedArrayConditions, aliasColObjMap, throwErrorIfInvalid, errors) {
    if (!nestedArrayConditions || nestedArrayConditions.length === 0) {
        return { filters: [] };
    }
    const parsedFilters = nestedArrayConditions
        .map((str) => {
        var _a, _b, _c;
        let logicOp;
        let alias;
        let op;
        let value;
        [logicOp, alias, op, value] =
            ((_a = str.match(/(?:~(and|or|not))?\((.*?),(\w+),(.*)\)/)) === null || _a === void 0 ? void 0 : _a.slice(1)) || [];
        if (!alias && !op && !value) {
            // Attempt to match blank filter format
            [logicOp, alias, op, value] =
                ((_b = str.match(/(?:~(and|or|not))?\((.*?),(\w+)\)/)) === null || _b === void 0 ? void 0 : _b.slice(1)) || [];
        }
        // Normalize filter operations
        switch (op) {
            case 'is':
                if (value === 'blank') {
                    op = 'blank';
                    value = undefined;
                }
                else if (value === 'notblank') {
                    op = 'notblank';
                    value = undefined;
                }
                break;
            case 'isblank':
            case 'is_blank':
                op = 'blank';
                break;
            case 'isnotblank':
            case 'is_not_blank':
            case 'is_notblank':
                op = 'notblank';
                break;
        }
        let sub_op = null;
        if (aliasColObjMap[alias]) {
            const columnType = aliasColObjMap[alias].uidt;
            // Handle date and datetime values
            if ([
                UITypes.Date,
                UITypes.DateTime,
                UITypes.LastModifiedTime,
                UITypes.CreatedTime,
            ].includes(columnType)) {
                value = value === null || value === void 0 ? void 0 : value.split(',');
                sub_op = value === null || value === void 0 ? void 0 : value.shift();
                value = value === null || value === void 0 ? void 0 : value[0];
                if (sub_op === 'null') {
                    sub_op = undefined;
                    value = null;
                }
            }
            else if (op === 'in') {
                value = value.split(',');
            }
            validateFilterComparison(columnType, op, sub_op, errors, throwErrorIfInvalid);
        }
        else {
            const error = {
                message: alias
                    ? `Column alias '${alias}' not found.`
                    : 'Invalid filter format.',
            };
            if (throwErrorIfInvalid)
                throw new NcSDKError(error.message);
            errors.push(error);
            return null;
        }
        let columnId = (_c = aliasColObjMap[alias]) === null || _c === void 0 ? void 0 : _c.id;
        // If alias is not found, check if it matches a column ID directly
        if (!columnId &&
            Object.values(aliasColObjMap).some((col) => (col === null || col === void 0 ? void 0 : col.id) === alias)) {
            columnId = alias;
        }
        return Object.assign(Object.assign({ comparison_op: op }, (sub_op && {
            comparison_sub_op: sub_op,
        })), { fk_column_id: columnId, logical_op: logicOp, value });
    })
        .filter(Boolean);
    if (errors.length > 0) {
        return { errors };
    }
    return { filters: parsedFilters };
}
//# sourceMappingURL=data:application/json;base64,eyJ2ZXJzaW9uIjozLCJmaWxlIjoiZmlsdGVySGVscGVyc19vbGQuanMiLCJzb3VyY2VSb290IjoiIiwic291cmNlcyI6WyIuLi8uLi8uLi9zcmMvbGliL2ZpbHRlckhlbHBlcnNfb2xkLnRzIl0sIm5hbWVzIjpbXSwibWFwcGluZ3MiOiJBQUNBLE9BQU8sRUFBRSxVQUFVLEVBQUUsVUFBVSxFQUFFLE1BQU0sa0JBQWtCLENBQUM7QUFDMUQsT0FBTyxFQUNMLGNBQWMsRUFDZCxrQkFBa0IsRUFFbEIsc0JBQXNCLEVBQ3RCLDRCQUE0QixFQUM1QixPQUFPLEdBQ1IsTUFBTSxhQUFhLENBQUM7QUFDckIsT0FBTyxFQUNMLGNBQWMsRUFDZCxrQkFBa0IsRUFDbEIsc0JBQXNCLEVBQ3RCLDRCQUE0QixHQUM3QixNQUFNLDZDQUE2QyxDQUFDO0FBRXJELE1BQU0sVUFBVSx1QkFBdUIsQ0FDckMsR0FBc0IsRUFDdEIsY0FBcUQsRUFDckQsbUJBQW1CLEdBQUcsS0FBSyxFQUMzQixTQUE2QixFQUFFO0lBRS9CLElBQUksQ0FBQyxHQUFHLEVBQUUsQ0FBQztRQUNULE9BQU8sRUFBRSxPQUFPLEVBQUUsRUFBRSxFQUFFLENBQUM7SUFDekIsQ0FBQztJQUVELG1DQUFtQztJQUNuQyxJQUFJLEtBQUssQ0FBQyxPQUFPLENBQUMsR0FBRyxDQUFDLEVBQUUsQ0FBQztRQUN2QixNQUFNLGFBQWEsR0FBRyxHQUFHLENBQUMsR0FBRyxDQUFDLENBQUMsQ0FBQyxFQUFFLEVBQUUsQ0FDbEMsdUJBQXVCLENBQUMsQ0FBQyxFQUFFLGNBQWMsRUFBRSxtQkFBbUIsRUFBRSxNQUFNLENBQUMsQ0FDeEUsQ0FBQztRQUVGLE1BQU0sT0FBTyxHQUFHLGFBQWEsQ0FBQyxNQUFNLENBQUMsQ0FBQyxHQUFHLEVBQUUsRUFBRSxPQUFPLEVBQUUsRUFBRSxFQUFFO1lBQ3hELElBQUksQ0FBQyxPQUFPO2dCQUFFLE9BQU8sR0FBRyxDQUFDO1lBQ3pCLE9BQU8sQ0FBQyxHQUFHLEdBQUcsRUFBRSxHQUFHLE9BQU8sQ0FBQyxDQUFDO1FBQzlC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