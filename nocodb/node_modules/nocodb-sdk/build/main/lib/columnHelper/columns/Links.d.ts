import AbstractColumnHelper, { SerializerOrParserFnProps } from '../column.interface';
export declare class LinksHelper extends AbstractColumnHelper {
    columnDefaultMeta: {};
    serializeValue(value: any, params: SerializerOrParserFnProps['params']): Record<string, any> | null;
    parseValue(value: any, params: SerializerOrParserFnProps['params']): any;
    parsePlainCellValue(value: any, params: SerializerOrParserFnProps['params'] & {
        rowId: string;
    }): string;
}
