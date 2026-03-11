import type { AnonymizeOptions } from "../lib/api";

export const defaultOptions: AnonymizeOptions = {
  fio: true,
  passport: true,
  birthdate: true,
  snils_inn: true,
  phone: true,
  banking: true,
};

export const optionLabels: Array<{ key: keyof AnonymizeOptions; label: string }> = [
  { key: "fio", label: "ФИО" },
  { key: "passport", label: "Паспортные данные" },
  { key: "birthdate", label: "Даты рождения" },
  { key: "snils_inn", label: "СНИЛС / ИНН" },
  { key: "phone", label: "Телефоны" },
];
