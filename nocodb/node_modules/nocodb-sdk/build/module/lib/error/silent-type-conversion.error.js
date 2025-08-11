import { TypeConversionError } from './type-conversion.error';
export class SilentTypeConversionError extends TypeConversionError {
    constructor() {
        super('');
        this.isErrorSuppressed = true;
    }
}
//# sourceMappingURL=data:application/json;base64,eyJ2ZXJzaW9uIjozLCJmaWxlIjoic2lsZW50LXR5cGUtY29udmVyc2lvbi5lcnJvci5qcyIsInNvdXJjZVJvb3QiOiIiLCJzb3VyY2VzIjpbIi4uLy4uLy4uLy4uL3NyYy9saWIvZXJyb3Ivc2lsZW50LXR5cGUtY29udmVyc2lvbi5lcnJvci50cyJdLCJuYW1lcyI6W10sIm1hcHBpbmdzIjoiQUFDQSxPQUFPLEVBQUUsbUJBQW1CLEVBQUUsTUFBTSx5QkFBeUIsQ0FBQztBQUU5RCxNQUFNLE9BQU8seUJBQ1gsU0FBUSxtQkFBbUI7SUFHM0I7UUFDRSxLQUFLLENBQUMsRUFBRSxDQUFDLENBQUM7UUFDVixJQUFJLENBQUMsaUJBQWlCLEdBQUcsSUFBSSxDQUFDO0lBQ2hDLENBQUM7Q0FHRiJ9