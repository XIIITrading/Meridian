import type { SuppressedError } from './suppressed.error';
import { TypeConversionError } from './type-conversion.error';
export declare class SelectTypeConversionError extends TypeConversionError implements SuppressedError {
    readonly value: string[];
    readonly missingOptions: string[];
    constructor(value: string[], missingOptions: string[]);
    isErrorSuppressed: boolean;
}
