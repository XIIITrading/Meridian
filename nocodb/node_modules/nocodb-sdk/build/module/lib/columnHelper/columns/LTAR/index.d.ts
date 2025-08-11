import AbstractColumnHelper, { SerializerOrParserFnProps } from '../../column.interface';
import { BelongsToHelper } from './BelongsTo';
import { HasManyHelper } from './HasMany';
import { ManyToManyHelper } from './ManyToMany';
import { OneToOneHelper } from './OneToOne';
export declare class LTARHelper extends AbstractColumnHelper {
    columnDefaultMeta: {};
    getLtarHelperColumn(params: SerializerOrParserFnProps['params']): AbstractColumnHelper;
    serializeValue(value: any, params: SerializerOrParserFnProps['params']): any;
    parseValue(value: any, params: SerializerOrParserFnProps['params']): any;
    parsePlainCellValue(value: any, params: SerializerOrParserFnProps['params']): string;
}
export { BelongsToHelper, HasManyHelper, ManyToManyHelper, OneToOneHelper };
