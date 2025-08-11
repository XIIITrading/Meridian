import { SerializerOrParserFnProps } from '../column.interface';
import { SingleLineTextHelper } from './SingleLineText';
export declare class EmailHelper extends SingleLineTextHelper {
    columnDefaultMeta: {};
    serializeValue(value: any, params: SerializerOrParserFnProps['params']): string | null;
}
