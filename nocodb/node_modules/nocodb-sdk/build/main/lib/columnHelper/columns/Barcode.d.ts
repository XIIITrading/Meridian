import AbstractColumnHelper, { SerializerOrParserFnProps } from '../column.interface';
export declare class BarcodeHelper extends AbstractColumnHelper {
    columnDefaultMeta: {
        barcodeFormat: "CODE128";
    };
    serializeValue(_value: any, params: SerializerOrParserFnProps['params']): undefined;
    parseValue(value: any): string | null;
    parsePlainCellValue(value: any): string;
}
