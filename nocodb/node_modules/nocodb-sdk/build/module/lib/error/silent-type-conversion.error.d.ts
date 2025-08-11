import type { SuppressedError } from './suppressed.error';
import { TypeConversionError } from './type-conversion.error';
export declare class SilentTypeConversionError extends TypeConversionError implements SuppressedError {
    constructor();
    isErrorSuppressed: boolean;
}
