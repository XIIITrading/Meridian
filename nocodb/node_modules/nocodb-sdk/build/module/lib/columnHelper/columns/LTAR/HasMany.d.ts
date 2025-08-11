import AbstractColumnHelper, { SerializerOrParserFnProps } from '../../column.interface';
export declare class HasManyHelper extends AbstractColumnHelper {
    columnDefaultMeta: {};
    serializeValue(_value: any, _params: SerializerOrParserFnProps['params']): void;
    parseValue(value: any, _params: SerializerOrParserFnProps['params']): any;
    parsePlainCellValue(value: any, params: SerializerOrParserFnProps['params']): string;
}
