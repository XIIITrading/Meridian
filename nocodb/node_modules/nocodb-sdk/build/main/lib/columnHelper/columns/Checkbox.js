"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.CheckboxHelper = void 0;
const __1 = require("..");
const column_interface_1 = __importDefault(require("../column.interface"));
class CheckboxHelper extends column_interface_1.default {
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
        return (0, __1.serializeCheckboxValue)(value);
    }
    parseValue(value) {
        return (0, __1.parseCheckboxValue)(value);
    }
    parsePlainCellValue(value) {
        return (0, __1.parseCheckboxValue)(value) ? 'Checked' : 'Unchecked';
    }
}
exports.CheckboxHelper = CheckboxHelper;
//# sourceMappingURL=data:application/json;base64,eyJ2ZXJzaW9uIjozLCJmaWxlIjoiQ2hlY2tib3guanMiLCJzb3VyY2VSb290IjoiIiwic291cmNlcyI6WyIuLi8uLi8uLi8uLi8uLi9zcmMvbGliL2NvbHVtbkhlbHBlci9jb2x1bW5zL0NoZWNrYm94LnRzIl0sIm5hbWVzIjpbXSwibWFwcGluZ3MiOiI7Ozs7OztBQUFBLDBCQUFnRTtBQUNoRSwyRUFBdUQ7QUFFdkQsTUFBYSxjQUFlLFNBQVEsMEJBQW9CO0lBQXhEOztRQUNFLHNCQUFpQixHQUFHO1lBQ2xCLE9BQU8sRUFBRSxDQUFDO1lBQ1YsSUFBSSxFQUFFO2dCQUNKLE9BQU8sRUFBRSxnQkFBZ0I7Z0JBQ3pCLFNBQVMsRUFBRSxpQkFBaUI7YUFDN0I7WUFDRCxLQUFLLEVBQUUsTUFBTTtTQUNkLENBQUM7SUFhSixDQUFDO0lBWEMsY0FBYyxDQUFDLEtBQVU7UUFDdkIsT0FBTyxJQUFBLDBCQUFzQixFQUFDLEtBQUssQ0FBQyxDQUFDO0lBQ3ZDLENBQUM7SUFFRCxVQUFVLENBQUMsS0FBVTtRQUNuQixPQUFPLElBQUEsc0JBQWtCLEVBQUMsS0FBSyxDQUFDLENBQUM7SUFDbkMsQ0FBQztJQUVELG1CQUFtQixDQUFDLEtBQVU7UUFDNUIsT0FBTyxJQUFBLHNCQUFrQixFQUFDLEtBQUssQ0FBQyxDQUFDLENBQUMsQ0FBQyxTQUFTLENBQUMsQ0FBQyxDQUFDLFdBQVcsQ0FBQztJQUM3RCxDQUFDO0NBQ0Y7QUFyQkQsd0NBcUJDIn0=