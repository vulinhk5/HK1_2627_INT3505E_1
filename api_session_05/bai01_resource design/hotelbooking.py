#ROOM
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://api.hotel.example/schemas/room.json",
  "title": "Room",
  "type": "object",
  "properties": {
    "roomId": { "type": "integer", "minimum": 1, "readOnly": true },
    "roomTypeId": { "type": "integer", "minimum": 1 },
    "roomNumber": { "type": "string", "pattern": "^[0-9]{3,4}$", "description": "Số phòng, duy nhất trong khách sạn" },
    "floor": { "type": "integer", "minimum": 0, "maximum": 100 },
    "status": { "enum": ["active", "out_of_service"], "default": "active" }
  },
  "required": ["roomTypeId", "roomNumber", "floor"],
  "additionalProperties": false
}

#GUEST
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://api.hotel.example/schemas/guest.json",
  "title": "Guest",
  "type": "object",
  "properties": {
    "guestId": { "type": "integer", "minimum": 1, "readOnly": true },
    "fullName": { "type": "string", "minLength": 2, "maxLength": 100 },
    "email": { "type": "string", "format": "email", "maxLength": 254 },
    "phone": { "type": "string", "pattern": "^[+]?[0-9]{9,15}$" },
    "nationalId": { "type": "string", "pattern": "^[0-9A-Z]{8,15}$", "description": "Số CCCD hoặc hộ chiếu" },
    "createdAt": { "type": "string", "format": "date-time", "readOnly": true }
  },
  "required": ["fullName", "email", "phone"],
  "additionalProperties": false
}

#BOOKING
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://api.hotel.example/schemas/booking.json",
  "title": "Booking",
  "type": "object",
  "properties": {
    "bookingId": { "type": "integer", "minimum": 1, "readOnly": true },
    "guestId": { "type": "integer", "minimum": 1 },
    "roomId": { "type": "integer", "minimum": 1 },
    "checkIn": { "type": "string", "format": "date" },
    "checkOut": { "type": "string", "format": "date" },
    "numGuests": { "type": "integer", "minimum": 1, "maximum": 10 },
    "status": { "enum": ["pending", "confirmed", "checked_in", "checked_out", "cancelled"], "readOnly": true },
    "totalAmount": { "type": "integer", "minimum": 0, "readOnly": true, "description": "VND" },
    "note": { "type": "string", "maxLength": 500 },
    "createdAt": { "type": "string", "format": "date-time", "readOnly": true },
    "updatedAt": { "type": "string", "format": "date-time", "readOnly": true }
  },
  "required": ["guestId", "roomId", "checkIn", "checkOut", "numGuests"],
  "additionalProperties": false
}