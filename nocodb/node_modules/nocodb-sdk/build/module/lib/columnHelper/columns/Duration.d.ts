import AbstractColumnHelper, { SerializerOrParserFnProps } from '../column.interface';
export declare class DurationHelper extends AbstractColumnHelper {
    columnDefaultMeta: {
        duration: number;
    };
    serializeValue(value: any, params: SerializerOrParserFnProps['params']): number | null;
    parseValue(value: any, params: SerializerOrParserFnProps['params']): number | null;
    parsePlainCellValue(value: any, params: SerializerOrParserFnProps['params']): string;
}
