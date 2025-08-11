import { ColumnType, FilterType } from './Api';
export declare const testExtractFilterFromXwhere: (title: string, extractFilterFromXwhere: (str: string | string[], aliasColObjMap: {
    [columnAlias: string]: ColumnType;
}, throwErrorIfInvalid?: boolean) => {
    filters?: FilterType[];
    errors?: any;
}) => void;
