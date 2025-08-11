import AbstractColumnHelper, { SerializerOrParserFnProps } from '../column.interface';
export declare class RollupHelper extends AbstractColumnHelper {
    columnDefaultMeta: {
        precision: 0;
        isLocaleString: boolean;
    };
    serializeValue(_value: any, params: SerializerOrParserFnProps['params']): null;
    parseValue(value: any, params: SerializerOrParserFnProps['params']): string | null;
    parsePlainCellValue(value: any, params: SerializerOrParserFnProps['params']): string;
}
