export { COMPARISON_OPS, COMPARISON_SUB_OPS, GROUPBY_COMPARISON_OPS, IS_WITHIN_COMPARISON_SUB_OPS, } from '../lib/parser/queryFilter/query-filter-lexer';
import { extractFilterFromXwhere as parserExtract } from './filterHelpers_withparser';
import { extractFilterFromXwhere as oldExtract } from './filterHelpers_old';
import { NcApiVersion } from './enums';
/**
 * Converts a flat array of filter objects into a nested tree structure
 * @param {FilterType[]} items - Array of filter objects
 * @returns {FilterType[]} - Nested tree structure
 */
export function buildFilterTree(items) {
    const itemMap = new Map();
    const rootItems = [];
    // Map items with IDs and handle items without IDs
    items.forEach((item) => {
        if (item.id) {
            itemMap.set(item.id, Object.assign(Object.assign({}, item), { children: [] }));
        }
        else {
            // Items without IDs go straight to root level
            rootItems.push(Object.assign(Object.assign({}, item), { children: [] }));
        }
    });
    // Build parent-child relationships for items with IDs
    items.forEach((item) => {
        // Skip items without IDs as they're already in rootItems
        if (!item.id)
            return;
        const mappedItem = itemMap.get(item.id);
        if (item.fk_parent_id === null) {
            rootItems.push(mappedItem);
        }
        else {
            const parent = itemMap.get(item.fk_parent_id);
            if (parent) {
                parent.children.push(mappedItem);
            }
            else {
                // If parent is not found, treat as root item
                rootItems.push(mappedItem);
            }
        }
    });
    return rootItems;
}
export function extractFilterFromXwhere(context, str, aliasColObjMap, throwErrorIfInvalid = false, errors = []) {
    if (context.api_version === NcApiVersion.V3) {
        return parserExtract(str, aliasColObjMap, throwErrorIfInvalid, errors);
    }
    else if (typeof str === 'string' && str.startsWith('@')) {
        return parserExtract(str.substring(1), aliasColObjMap, throwErrorIfInvalid, errors);
    }
    else {
        return oldExtract(str, aliasColObjMap, throwErrorIfInvalid, errors);
    }
}
//# sourceMappingURL=data:application/json;base64,eyJ2ZXJzaW9uIjozLCJmaWxlIjoiZmlsdGVySGVscGVycy5qcyIsInNvdXJjZVJvb3QiOiIiLCJzb3VyY2VzIjpbIi4uLy4uLy4uL3NyYy9saWIvZmlsdGVySGVscGVycy50cyJdLCJuYW1lcyI6W10sIm1hcHBpbmdzIjoiQUFFQSxPQUFPLEVBQ0wsY0FBYyxFQUNkLGtCQUFrQixFQUNsQixzQkFBc0IsRUFDdEIsNEJBQTRCLEdBQzdCLE1BQU0sNkNBQTZDLENBQUM7QUFDckQsT0FBTyxFQUFFLHVCQUF1QixJQUFJLGFBQWEsRUFBRSxNQUFNLDRCQUE0QixDQUFDO0FBQ3RGLE9BQU8sRUFBRSx1QkFBdUIsSUFBSSxVQUFVLEVBQUUsTUFBTSxxQkFBcUIsQ0FBQztBQUU1RSxPQUFPLEVBQUUsWUFBWSxFQUFFLE1BQU0sU0FBUyxDQUFDO0FBTXZDOzs7O0dBSUc7QUFDSCxNQUFNLFVBQVUsZUFBZSxDQUFDLEtBQW1CO0lBQ2pELE1BQU0sT0FBTyxHQUFHLElBQUksR0FBRyxFQUFFLENBQUM7SUFDMUIsTUFBTSxTQUFTLEdBQWlCLEVBQUUsQ0FBQztJQUVuQyxrREFBa0Q7SUFDbEQsS0FBSyxDQUFDLE9BQU8sQ0FBQyxDQUFDLElBQUksRUFBRSxFQUFFO1FBQ3JCLElBQUksSUFBSSxDQUFDLEVBQUUsRUFBRSxDQUFDO1lBQ1osT0FBTyxDQUFDLEdBQUcsQ0FBQyxJQUFJLENBQUMsRUFBRSxrQ0FBTyxJQUFJLEtBQUUsUUFBUSxFQUFFLEVBQUUsSUFBRyxDQUFDO1FBQ2xELENBQUM7YUFBTSxDQUFDO1lBQ04sOENBQThDO1lBQzlDLFNBQVMsQ0FBQyxJQUFJLGlDQUFNLElBQUksS0FBRSxRQUFRLEVBQUUsRUFBRSxJQUFHLENBQUM7UUFDNUMsQ0FBQztJQUNILENBQUMsQ0FBQyxDQUFDO0lBRUgsc0RBQXNEO0lBQ3RELEtBQUssQ0FBQyxPQUFPLENBQUMsQ0FBQyxJQUFJLEVBQUUsRUFBRTtRQUNyQix5REFBeUQ7UUFDekQsSUFBSSxDQUFDLElBQUksQ0FBQyxFQUFFO1lBQUUsT0FBTztRQUVyQixNQUFNLFVBQVUsR0FBRyxPQUFPLENBQUMsR0FBRyxDQUFDLElBQUksQ0FBQyxFQUFFLENBQUMsQ0FBQztRQUV4QyxJQUFJLElBQUksQ0FBQyxZQUFZLEtBQUssSUFBSSxFQUFFLENBQUM7WUFDL0IsU0FBUyxDQUFDLElBQUksQ0FBQyxVQUFVLENBQUMsQ0FBQztRQUM3QixDQUFDO2FBQU0sQ0FBQztZQUNOLE1BQU0sTUFBTSxHQUFHLE9BQU8sQ0FBQyxHQUFHLENBQUMsSUFBSSxDQUFDLFlBQVksQ0FBQyxDQUFDO1lBQzlDLElBQUksTUFBTSxFQUFFLENBQUM7Z0JBQ1gsTUFBTSxDQUFDLFFBQVEsQ0FBQyxJQUFJLENBQUMsVUFBVSxDQUFDLENBQUM7WUFDbkMsQ0FBQztpQkFBTSxDQUFDO2dCQUNOLDZDQUE2QztnQkFDN0MsU0FBUyxDQUFDLElBQUksQ0FBQyxVQUFVLENBQUMsQ0FBQztZQUM3QixDQUFDO1FBQ0gsQ0FBQztJQUNILENBQUMsQ0FBQyxDQUFDO0lBRUgsT0FBTyxTQUFTLENBQUM7QUFDbkIsQ0FBQztBQUVELE1BQU0sVUFBVSx1QkFBdUIsQ0FDckMsT0FBdUMsRUFDdkMsR0FBc0IsRUFDdEIsY0FBcUQsRUFDckQsbUJBQW1CLEdBQUcsS0FBSyxFQUMzQixTQUE2QixFQUFFO0lBRS9CLElBQUksT0FBTyxDQUFDLFdBQVcsS0FBSyxZQUFZLENBQUMsRUFBRSxFQUFFLENBQUM7UUFDNUMsT0FBTyxhQUFhLENBQUMsR0FBRyxFQUFFLGNBQWMsRUFBRSxtQkFBbUIsRUFBRSxNQUFNLENBQUMsQ0FBQztJQUN6RSxDQUFDO1NBQU0sSUFBSSxPQUFPLEdBQUcsS0FBSyxRQUFRLElBQUksR0FBRyxDQUFDLFVBQVUsQ0FBQyxHQUFHLENBQUMsRUFBRSxDQUFDO1FBQzFELE9BQU8sYUFBYSxDQUNsQixHQUFHLENBQUMsU0FBUyxDQUFDLENBQUMsQ0FBQyxFQUNoQixjQUFjLEVBQ2QsbUJBQW1CLEVBQ25CLE1BQU0sQ0FDUCxDQUFDO0lBQ0osQ0FBQztTQUFNLENBQUM7UUFDTixPQUFPLFVBQVUsQ0FBQyxHQUFHLEVBQUUsY0FBYyxFQUFFLG1CQUFtQixFQUFFLE1BQU0sQ0FBQyxDQUFDO0lBQ3RFLENBQUM7QUFDSCxDQUFDIn0=