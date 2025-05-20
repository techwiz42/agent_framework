import { format, isToday, isYesterday } from 'date-fns';

export const formatMessageDate = (timestamp: string): string => {
  const date = new Date(timestamp);
  if (isToday(date)) {
    return format(date, "'Today at' h:mm a");
  }
  if (isYesterday(date)) {
    return format(date, "'Yesterday at' h:mm a");
  }
  return format(date, "MMM d 'at' h:mm a");
};

export const formatDateSeparator = (timestamp: string): string => {
  const date = new Date(timestamp);
  if (isToday(date)) {
    return 'Today';
  }
  if (isYesterday(date)) {
    return 'Yesterday';
  }
  return format(date, 'MMMM d, yyyy');
};
