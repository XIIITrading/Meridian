import UITypes from '../../../lib/UITypes';
export function getLookupColumnType({ col, meta, metas, visitedIds = new Set(), }) {
    var _a, _b;
    const colOptions = col.colOptions;
    const relationColumnOptions = colOptions.fk_relation_column_id
        ? (_b = (_a = meta === null || meta === void 0 ? void 0 : meta.columns) === null || _a === void 0 ? void 0 : _a.find((c) => c.id === colOptions.fk_relation_column_id)) === null || _b === void 0 ? void 0 : _b.colOptions
        : null;
    const relatedTableMeta = (relationColumnOptions === null || relationColumnOptions === void 0 ? void 0 : relationColumnOptions.fk_related_model_id) &&
        (metas === null || metas === void 0 ? void 0 : metas[relationColumnOptions.fk_related_model_id]);
    const childColumn = relatedTableMeta === null || relatedTableMeta === void 0 ? void 0 : relatedTableMeta.columns.find((c) => c.id === colOptions.fk_lookup_column_id);
    // if child column is lookup column, then recursively find the column type
    // and check for circular dependency
    if (childColumn &&
        childColumn.uidt === UITypes.Lookup &&
        !visitedIds.has(childColumn.id)) {
        visitedIds.add(childColumn.id);
        return getLookupColumnType({
            col: childColumn,
            meta: relatedTableMeta,
            metas: metas,
            visitedIds: visitedIds,
        });
    }
    return (childColumn === null || childColumn === void 0 ? void 0 : childColumn.uidt) || null;
}
//# sourceMappingURL=data:application/json;base64,eyJ2ZXJzaW9uIjozLCJmaWxlIjoiZ2V0LWxvb2t1cC1jb2x1bW4tdHlwZS5qcyIsInNvdXJjZVJvb3QiOiIiLCJzb3VyY2VzIjpbIi4uLy4uLy4uLy4uLy4uL3NyYy9saWIvY29sdW1uSGVscGVyL3V0aWxzL2dldC1sb29rdXAtY29sdW1uLXR5cGUudHMiXSwibmFtZXMiOltdLCJtYXBwaW5ncyI6IkFBQ0EsT0FBTyxPQUFPLE1BQU0sZUFBZSxDQUFDO0FBRXBDLE1BQU0sVUFBVSxtQkFBbUIsQ0FBQyxFQUNsQyxHQUFHLEVBQ0gsSUFBSSxFQUNKLEtBQUssRUFDTCxVQUFVLEdBQUcsSUFBSSxHQUFHLEVBQVUsR0FNL0I7O0lBQ0MsTUFBTSxVQUFVLEdBQUcsR0FBRyxDQUFDLFVBQXdCLENBQUM7SUFDaEQsTUFBTSxxQkFBcUIsR0FBUSxVQUFVLENBQUMscUJBQXFCO1FBQ2pFLENBQUMsQ0FBQyxNQUFBLE1BQUEsSUFBSSxhQUFKLElBQUksdUJBQUosSUFBSSxDQUFFLE9BQU8sMENBQUUsSUFBSSxDQUFDLENBQUMsQ0FBQyxFQUFFLEVBQUUsQ0FBQyxDQUFDLENBQUMsRUFBRSxLQUFLLFVBQVUsQ0FBQyxxQkFBcUIsQ0FBQywwQ0FDakUsVUFBVTtRQUNoQixDQUFDLENBQUMsSUFBSSxDQUFDO0lBQ1QsTUFBTSxnQkFBZ0IsR0FDcEIsQ0FBQSxxQkFBcUIsYUFBckIscUJBQXFCLHVCQUFyQixxQkFBcUIsQ0FBRSxtQkFBbUI7U0FDMUMsS0FBSyxhQUFMLEtBQUssdUJBQUwsS0FBSyxDQUFHLHFCQUFxQixDQUFDLG1CQUE2QixDQUFDLENBQUEsQ0FBQztJQUUvRCxNQUFNLFdBQVcsR0FBRyxnQkFBZ0IsYUFBaEIsZ0JBQWdCLHVCQUFoQixnQkFBZ0IsQ0FBRSxPQUFPLENBQUMsSUFBSSxDQUNoRCxDQUFDLENBQWEsRUFBRSxFQUFFLENBQUMsQ0FBQyxDQUFDLEVBQUUsS0FBSyxVQUFVLENBQUMsbUJBQW1CLENBQ2pDLENBQUM7SUFFNUIsMEVBQTBFO0lBQzFFLG9DQUFvQztJQUNwQyxJQUNFLFdBQVc7UUFDWCxXQUFXLENBQUMsSUFBSSxLQUFLLE9BQU8sQ0FBQyxNQUFNO1FBQ25DLENBQUMsVUFBVSxDQUFDLEdBQUcsQ0FBQyxXQUFXLENBQUMsRUFBRSxDQUFDLEVBQy9CLENBQUM7UUFDRCxVQUFVLENBQUMsR0FBRyxDQUFDLFdBQVcsQ0FBQyxFQUFFLENBQUMsQ0FBQztRQUMvQixPQUFPLG1CQUFtQixDQUFDO1lBQ3pCLEdBQUcsRUFBRSxXQUFXO1lBQ2hCLElBQUksRUFBRSxnQkFBZ0I7WUFDdEIsS0FBSyxFQUFFLEtBQUs7WUFDWixVQUFVLEVBQUUsVUFBVTtTQUN2QixDQUFDLENBQUM7SUFDTCxDQUFDO0lBRUQsT0FBTyxDQUFDLFdBQVcsYUFBWCxXQUFXLHVCQUFYLFdBQVcsQ0FBRSxJQUFnQixLQUFJLElBQUksQ0FBQztBQUNoRCxDQUFDIn0=