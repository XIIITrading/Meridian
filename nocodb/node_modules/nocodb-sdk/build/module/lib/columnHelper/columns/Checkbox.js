import { parseCheckboxValue, serializeCheckboxValue } from '..';
import AbstractColumnHelper from '../column.interface';
export class CheckboxHelper extends AbstractColumnHelper {
    constructor() {
        super(...arguments);
        this.columnDefaultMeta = {
            iconIdx: 0,
            icon: {
                checked: 'mdi-check-bold',
                unchecked: 'mdi-crop-square',
            },
            color: '#777',
        };
    }
    serializeValue(value) {
        return serializeCheckboxValue(value);
    }
    parseValue(value) {
        return parseCheckboxValue(value);
    }
    parsePlainCellValue(value) {
        return parseCheckboxValue(value) ? 'Checked' : 'Unchecked';
    }
}
//# sourceMappingURL=data:application/json;base64,eyJ2ZXJzaW9uIjozLCJmaWxlIjoiQ2hlY2tib3guanMiLCJzb3VyY2VSb290IjoiIiwic291cmNlcyI6WyIuLi8uLi8uLi8uLi8uLi9zcmMvbGliL2NvbHVtbkhlbHBlci9jb2x1bW5zL0NoZWNrYm94LnRzIl0sIm5hbWVzIjpbXSwibWFwcGluZ3MiOiJBQUFBLE9BQU8sRUFBRSxrQkFBa0IsRUFBRSxzQkFBc0IsRUFBRSxNQUFNLElBQUksQ0FBQztBQUNoRSxPQUFPLG9CQUFvQixNQUFNLHFCQUFxQixDQUFDO0FBRXZELE1BQU0sT0FBTyxjQUFlLFNBQVEsb0JBQW9CO0lBQXhEOztRQUNFLHNCQUFpQixHQUFHO1lBQ2xCLE9BQU8sRUFBRSxDQUFDO1lBQ1YsSUFBSSxFQUFFO2dCQUNKLE9BQU8sRUFBRSxnQkFBZ0I7Z0JBQ3pCLFNBQVMsRUFBRSxpQkFBaUI7YUFDN0I7WUFDRCxLQUFLLEVBQUUsTUFBTTtTQUNkLENBQUM7SUFhSixDQUFDO0lBWEMsY0FBYyxDQUFDLEtBQVU7UUFDdkIsT0FBTyxzQkFBc0IsQ0FBQyxLQUFLLENBQUMsQ0FBQztJQUN2QyxDQUFDO0lBRUQsVUFBVSxDQUFDLEtBQVU7UUFDbkIsT0FBTyxrQkFBa0IsQ0FBQyxLQUFLLENBQUMsQ0FBQztJQUNuQyxDQUFDO0lBRUQsbUJBQW1CLENBQUMsS0FBVTtRQUM1QixPQUFPLGtCQUFrQixDQUFDLEtBQUssQ0FBQyxDQUFDLENBQUMsQ0FBQyxTQUFTLENBQUMsQ0FBQyxDQUFDLFdBQVcsQ0FBQztJQUM3RCxDQUFDO0NBQ0YifQ==