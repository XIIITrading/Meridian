import { ColumnType } from '../../../lib/Api';
import UITypes from '../../../lib/UITypes';
export declare function getLookupColumnType({ col, meta, metas, visitedIds, }: {
    col: ColumnType;
    meta: {
        columns: ColumnType[];
    };
    metas: Record<string, any>;
    visitedIds?: Set<string>;
}): UITypes | null | undefined;
