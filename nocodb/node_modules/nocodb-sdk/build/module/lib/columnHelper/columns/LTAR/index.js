import AbstractColumnHelper from '../../column.interface';
import { isBt, isHm, isMm, isOo } from '../../utils';
import { DefaultColumnHelper } from '../DefaultColumnHelper';
import { BelongsToHelper } from './BelongsTo';
import { HasManyHelper } from './HasMany';
import { ManyToManyHelper } from './ManyToMany';
import { OneToOneHelper } from './OneToOne';
export class LTARHelper extends AbstractColumnHelper {
    constructor() {
        super(...arguments);
        this.columnDefaultMeta = {};
    }
    getLtarHelperColumn(params) {
        let columnHelper = DefaultColumnHelper;
        if (isHm(params.col))
            columnHelper = HasManyHelper;
        if (isMm(params.col))
            columnHelper = ManyToManyHelper;
        if (isBt(params.col))
            columnHelper = BelongsToHelper;
        if (isOo(params.col))
            columnHelper = OneToOneHelper;
        return new columnHelper();
    }
    serializeValue(value, params) {
        return this.getLtarHelperColumn(params).serializeValue(value, params);
    }
    parseValue(value, params) {
        return this.getLtarHelperColumn(params).parseValue(value, params);
    }
    parsePlainCellValue(value, params) {
        return this.getLtarHelperColumn(params).parsePlainCellValue(value, params);
    }
}
export { BelongsToHelper, HasManyHelper, ManyToManyHelper, OneToOneHelper };
//# sourceMappingURL=data:application/json;base64,eyJ2ZXJzaW9uIjozLCJmaWxlIjoiaW5kZXguanMiLCJzb3VyY2VSb290IjoiIiwic291cmNlcyI6WyIuLi8uLi8uLi8uLi8uLi8uLi9zcmMvbGliL2NvbHVtbkhlbHBlci9jb2x1bW5zL0xUQVIvaW5kZXgudHMiXSwibmFtZXMiOltdLCJtYXBwaW5ncyI6IkFBQUEsT0FBTyxvQkFFTixNQUFNLHdCQUF3QixDQUFDO0FBQ2hDLE9BQU8sRUFBRSxJQUFJLEVBQUUsSUFBSSxFQUFFLElBQUksRUFBRSxJQUFJLEVBQUUsTUFBTSxhQUFhLENBQUM7QUFDckQsT0FBTyxFQUFFLG1CQUFtQixFQUFFLE1BQU0sd0JBQXdCLENBQUM7QUFDN0QsT0FBTyxFQUFFLGVBQWUsRUFBRSxNQUFNLGFBQWEsQ0FBQztBQUM5QyxPQUFPLEVBQUUsYUFBYSxFQUFFLE1BQU0sV0FBVyxDQUFDO0FBQzFDLE9BQU8sRUFBRSxnQkFBZ0IsRUFBRSxNQUFNLGNBQWMsQ0FBQztBQUNoRCxPQUFPLEVBQUUsY0FBYyxFQUFFLE1BQU0sWUFBWSxDQUFDO0FBRTVDLE1BQU0sT0FBTyxVQUFXLFNBQVEsb0JBQW9CO0lBQXBEOztRQUNFLHNCQUFpQixHQUFHLEVBQUUsQ0FBQztJQTZCekIsQ0FBQztJQTNCQyxtQkFBbUIsQ0FDakIsTUFBMkM7UUFFM0MsSUFBSSxZQUFZLEdBQW1DLG1CQUFtQixDQUFDO1FBRXZFLElBQUksSUFBSSxDQUFDLE1BQU0sQ0FBQyxHQUFHLENBQUM7WUFBRSxZQUFZLEdBQUcsYUFBYSxDQUFDO1FBQ25ELElBQUksSUFBSSxDQUFDLE1BQU0sQ0FBQyxHQUFHLENBQUM7WUFBRSxZQUFZLEdBQUcsZ0JBQWdCLENBQUM7UUFDdEQsSUFBSSxJQUFJLENBQUMsTUFBTSxDQUFDLEdBQUcsQ0FBQztZQUFFLFlBQVksR0FBRyxlQUFlLENBQUM7UUFDckQsSUFBSSxJQUFJLENBQUMsTUFBTSxDQUFDLEdBQUcsQ0FBQztZQUFFLFlBQVksR0FBRyxjQUFjLENBQUM7UUFFcEQsT0FBTyxJQUFJLFlBQVksRUFBRSxDQUFDO0lBQzVCLENBQUM7SUFFRCxjQUFjLENBQUMsS0FBVSxFQUFFLE1BQTJDO1FBQ3BFLE9BQU8sSUFBSSxDQUFDLG1CQUFtQixDQUFDLE1BQU0sQ0FBQyxDQUFDLGNBQWMsQ0FBQyxLQUFLLEVBQUUsTUFBTSxDQUFDLENBQUM7SUFDeEUsQ0FBQztJQUVELFVBQVUsQ0FBQyxLQUFVLEVBQUUsTUFBMkM7UUFDaEUsT0FBTyxJQUFJLENBQUMsbUJBQW1CLENBQUMsTUFBTSxDQUFDLENBQUMsVUFBVSxDQUFDLEtBQUssRUFBRSxNQUFNLENBQUMsQ0FBQztJQUNwRSxDQUFDO0lBRUQsbUJBQW1CLENBQ2pCLEtBQVUsRUFDVixNQUEyQztRQUUzQyxPQUFPLElBQUksQ0FBQyxtQkFBbUIsQ0FBQyxNQUFNLENBQUMsQ0FBQyxtQkFBbUIsQ0FBQyxLQUFLLEVBQUUsTUFBTSxDQUFDLENBQUM7SUFDN0UsQ0FBQztDQUNGO0FBRUQsT0FBTyxFQUFFLGVBQWUsRUFBRSxhQUFhLEVBQUUsZ0JBQWdCLEVBQUUsY0FBYyxFQUFFLENBQUMifQ==