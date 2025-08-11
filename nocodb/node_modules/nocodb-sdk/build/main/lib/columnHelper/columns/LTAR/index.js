"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.OneToOneHelper = exports.ManyToManyHelper = exports.HasManyHelper = exports.BelongsToHelper = exports.LTARHelper = void 0;
const column_interface_1 = __importDefault(require("../../column.interface"));
const utils_1 = require("../../utils");
const DefaultColumnHelper_1 = require("../DefaultColumnHelper");
const BelongsTo_1 = require("./BelongsTo");
Object.defineProperty(exports, "BelongsToHelper", { enumerable: true, get: function () { return BelongsTo_1.BelongsToHelper; } });
const HasMany_1 = require("./HasMany");
Object.defineProperty(exports, "HasManyHelper", { enumerable: true, get: function () { return HasMany_1.HasManyHelper; } });
const ManyToMany_1 = require("./ManyToMany");
Object.defineProperty(exports, "ManyToManyHelper", { enumerable: true, get: function () { return ManyToMany_1.ManyToManyHelper; } });
const OneToOne_1 = require("./OneToOne");
Object.defineProperty(exports, "OneToOneHelper", { enumerable: true, get: function () { return OneToOne_1.OneToOneHelper; } });
class LTARHelper extends column_interface_1.default {
    constructor() {
        super(...arguments);
        this.columnDefaultMeta = {};
    }
    getLtarHelperColumn(params) {
        let columnHelper = DefaultColumnHelper_1.DefaultColumnHelper;
        if ((0, utils_1.isHm)(params.col))
            columnHelper = HasMany_1.HasManyHelper;
        if ((0, utils_1.isMm)(params.col))
            columnHelper = ManyToMany_1.ManyToManyHelper;
        if ((0, utils_1.isBt)(params.col))
            columnHelper = BelongsTo_1.BelongsToHelper;
        if ((0, utils_1.isOo)(params.col))
            columnHelper = OneToOne_1.OneToOneHelper;
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
exports.LTARHelper = LTARHelper;
//# sourceMappingURL=data:application/json;base64,eyJ2ZXJzaW9uIjozLCJmaWxlIjoiaW5kZXguanMiLCJzb3VyY2VSb290IjoiIiwic291cmNlcyI6WyIuLi8uLi8uLi8uLi8uLi8uLi9zcmMvbGliL2NvbHVtbkhlbHBlci9jb2x1bW5zL0xUQVIvaW5kZXgudHMiXSwibmFtZXMiOltdLCJtYXBwaW5ncyI6Ijs7Ozs7O0FBQUEsOEVBRWdDO0FBQ2hDLHVDQUFxRDtBQUNyRCxnRUFBNkQ7QUFDN0QsMkNBQThDO0FBcUNyQyxnR0FyQ0EsMkJBQWUsT0FxQ0E7QUFwQ3hCLHVDQUEwQztBQW9DaEIsOEZBcENqQix1QkFBYSxPQW9DaUI7QUFuQ3ZDLDZDQUFnRDtBQW1DUCxpR0FuQ2hDLDZCQUFnQixPQW1DZ0M7QUFsQ3pELHlDQUE0QztBQWtDZSwrRkFsQ2xELHlCQUFjLE9Ba0NrRDtBQWhDekUsTUFBYSxVQUFXLFNBQVEsMEJBQW9CO0lBQXBEOztRQUNFLHNCQUFpQixHQUFHLEVBQUUsQ0FBQztJQTZCekIsQ0FBQztJQTNCQyxtQkFBbUIsQ0FDakIsTUFBMkM7UUFFM0MsSUFBSSxZQUFZLEdBQW1DLHlDQUFtQixDQUFDO1FBRXZFLElBQUksSUFBQSxZQUFJLEVBQUMsTUFBTSxDQUFDLEdBQUcsQ0FBQztZQUFFLFlBQVksR0FBRyx1QkFBYSxDQUFDO1FBQ25ELElBQUksSUFBQSxZQUFJLEVBQUMsTUFBTSxDQUFDLEdBQUcsQ0FBQztZQUFFLFlBQVksR0FBRyw2QkFBZ0IsQ0FBQztRQUN0RCxJQUFJLElBQUEsWUFBSSxFQUFDLE1BQU0sQ0FBQyxHQUFHLENBQUM7WUFBRSxZQUFZLEdBQUcsMkJBQWUsQ0FBQztRQUNyRCxJQUFJLElBQUEsWUFBSSxFQUFDLE1BQU0sQ0FBQyxHQUFHLENBQUM7WUFBRSxZQUFZLEdBQUcseUJBQWMsQ0FBQztRQUVwRCxPQUFPLElBQUksWUFBWSxFQUFFLENBQUM7SUFDNUIsQ0FBQztJQUVELGNBQWMsQ0FBQyxLQUFVLEVBQUUsTUFBMkM7UUFDcEUsT0FBTyxJQUFJLENBQUMsbUJBQW1CLENBQUMsTUFBTSxDQUFDLENBQUMsY0FBYyxDQUFDLEtBQUssRUFBRSxNQUFNLENBQUMsQ0FBQztJQUN4RSxDQUFDO0lBRUQsVUFBVSxDQUFDLEtBQVUsRUFBRSxNQUEyQztRQUNoRSxPQUFPLElBQUksQ0FBQyxtQkFBbUIsQ0FBQyxNQUFNLENBQUMsQ0FBQyxVQUFVLENBQUMsS0FBSyxFQUFFLE1BQU0sQ0FBQyxDQUFDO0lBQ3BFLENBQUM7SUFFRCxtQkFBbUIsQ0FDakIsS0FBVSxFQUNWLE1BQTJDO1FBRTNDLE9BQU8sSUFBSSxDQUFDLG1CQUFtQixDQUFDLE1BQU0sQ0FBQyxDQUFDLG1CQUFtQixDQUFDLEtBQUssRUFBRSxNQUFNLENBQUMsQ0FBQztJQUM3RSxDQUFDO0NBQ0Y7QUE5QkQsZ0NBOEJDIn0=