import AbstractColumnHelper, { SerializerOrParserFnProps } from '../column.interface';
export declare class AttachmentHelper extends AbstractColumnHelper {
    columnDefaultMeta: {};
    serializeValue(value: any, params: SerializerOrParserFnProps['params']): any[];
    parseValue(value: any): boolean;
    parsePlainCellValue(value: any): string;
}
