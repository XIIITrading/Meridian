import { SerializerOrParserFnProps } from '../column.interface';
import { DateTimeHelper } from './DateTime';
export declare class CreatedTimeHelper extends DateTimeHelper {
    serializeValue(_value: any, _params: SerializerOrParserFnProps['params']): string | null;
}
