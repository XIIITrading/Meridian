import AbstractColumnHelper, { SerializerOrParserFnProps } from '../../column.interface';
export declare class ManyToManyHelper extends AbstractColumnHelper {
    columnDefaultMeta: {};
    serializeValue(value: any, params: SerializerOrParserFnProps['params']): {
        value: any;
        rowId: any;
        columnId: any;
        fk_related_model_id: any;
    };
    parseValue(value: any, params: SerializerOrParserFnProps['params']): string;
    parsePlainCellValue(value: any, params: SerializerOrParserFnProps['params']): string;
}
