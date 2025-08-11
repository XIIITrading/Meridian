import AbstractColumnHelper from '../column.interface';
export declare class CheckboxHelper extends AbstractColumnHelper {
    columnDefaultMeta: {
        iconIdx: number;
        icon: {
            checked: string;
            unchecked: string;
        };
        color: string;
    };
    serializeValue(value: any): boolean;
    parseValue(value: any): boolean;
    parsePlainCellValue(value: any): string;
}
