import AbstractColumnHelper, { SerializerOrParserFnProps } from '../column.interface';
export declare class SingleSelectHelper extends AbstractColumnHelper {
    columnDefaultMeta: {};
    serializeValue(value: any, params: SerializerOrParserFnProps['params']): string;
    parseValue(value: any): string | null;
    parsePlainCellValue(value: any): string;
}
