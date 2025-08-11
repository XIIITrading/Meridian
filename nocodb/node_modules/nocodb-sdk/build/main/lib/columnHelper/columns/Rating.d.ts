import AbstractColumnHelper, { SerializerOrParserFnProps } from '../column.interface';
export declare class RatingHelper extends AbstractColumnHelper {
    columnDefaultMeta: {
        iconIdx: number;
        icon: {
            full: string;
            empty: string;
        };
        color: string;
        max: number;
    };
    serializeValue(value: any, params: SerializerOrParserFnProps['params']): number | null;
    parseValue(value: any): string | number | null;
    parsePlainCellValue(value: any, params: SerializerOrParserFnProps['params']): string;
}
