import AbstractColumnHelper, { SerializerOrParserFnProps } from '../../column.interface';
export declare class OneToOneHelper extends AbstractColumnHelper {
    columnDefaultMeta: {};
    serializeValue(value: any, params: SerializerOrParserFnProps['params']): Record<string, any> | null;
    parseValue(value: any, params: SerializerOrParserFnProps['params']): string;
    parsePlainCellValue(value: any, params: SerializerOrParserFnProps['params']): string;
}
