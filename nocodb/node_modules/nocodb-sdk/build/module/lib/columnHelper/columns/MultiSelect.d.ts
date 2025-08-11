import AbstractColumnHelper, { SerializerOrParserFnProps } from '../column.interface';
export declare class MultiSelectHelper extends AbstractColumnHelper {
    columnDefaultMeta: {};
    serializeValue(value: any, params: SerializerOrParserFnProps['params']): string;
    parseValue(value: any): string | null;
    parsePlainCellValue(value: any): string;
}
