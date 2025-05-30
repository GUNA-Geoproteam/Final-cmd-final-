# # pdf_converter.py

# import os
# import logging
# from openpyxl import load_workbook
# from openpyxl.utils import get_column_letter
# from fpdf import FPDF
# import pandas as pd
# from customer_utils import get_customer_logo
# from excel_formatter import scale_to_fit



# import os
# from openpyxl import load_workbook
# from fpdf import FPDF
# from datetime import datetime
# from alignment_utils import load_alignment_dict





# # alignment_dict = {
# #     "Activity Summary by Month Report": {1: {"align": "L", "width": 25}, 2: {"align": "C", "width": 25}, 3: {"align": "C", "width": 30}, 4: {"align": "C", "width": 50}, 5: {"align": "C", "width": 50}},
# #     "CLAIMS BILLED REPORT": {1: {"align": "L", "width": 23}, 2: {"align": "C", "width": 40}, 3: {"align": "C", "width": 32}, 4: {"align": "C", "width": 30}, 5: {"align": "C", "width": 32}, 6: {"align": "C", "width": 40}, 7: {"align": "C", "width": 30}, 8: {"align": "C", "width": 30}, 9: {"align": "L", "width": 41}, 10: {"align": "L", "width": 95}, 11: {"align": "R", "width": 82}},
# #     "NEXTUS MONTHLY DETAIL PAYMENT REPORT": {1: {"align": "L", "width": 60}, 2: {"align": "C", "width": 27}, 3: {"align": "C", "width": 28}, 4: {"align": "L", "width": 50}, 5: {"align": "L", "width": 25}, 6: {"align": "C", "width": 30}, 7: {"align": "C", "width": 20}, 8: {"align": "C", "width": 29}, 9: {"align": "C", "width": 27}, 10: {"align": "C", "width": 30}, 11: {"align": "C", "width": 30}, 12: {"align": "L", "width": 75}, 13: {"align": "R", "width": 25}, 14: {"align": "C", "width": 19}},
# #     "NEXTUS PAYMENT SUMMARY MONTHLY REPORT": {1: {"align": "L", "width": 127}, 2: {"align": "C", "width": 42}, 3: {"align": "C", "width": 45}, 4: {"align": "C", "width": 42}, 5: {"align": "L", "width": 127}, 6: {"align": "C", "width": 37}, 7: {"align": "R", "width": 38}},
# #     "NEXTUS PAYMENT SUMMARY WEEKLY REPORT": {1: {"align": "L", "width": 127}, 2: {"align": "C", "width": 42}, 3: {"align": "C", "width": 45}, 4: {"align": "C", "width": 37}, 5: {"align": "L", "width": 135}, 6: {"align": "C", "width": 37}, 7: {"align": "R", "width": 38}},
# #     "AR AGING SUMMARY": {1: {"align": "L", "width": 135}, 2: {"align": "C", "width": 63}, 3: {"align": "C", "width": 49}, 4: {"align": "C", "width": 42}, 5: {"align": "C", "width": 42}, 6: {"align": "C", "width": 70}, 7: {"align": "C", "width": 43}, 8: {"align": "C", "width": 45}, 9: {"align": "C", "width": 38}, 10: {"align": "C", "width": 35}, 11: {"align": "C", "width": 35}},
# #     "NEXTUS PATIENT BALANCE REPORT": {1: {"align": "L", "width": 17}, 2: {"align": "C", "width": 65}, 3: {"align": "C", "width": 35}, 4: {"align": "L", "width": 27}, 5: {"align": "L", "width": 35}, 6: {"align": "C", "width": 35}, 7: {"align": "C", "width": 35}, 8: {"align": "C", "width": 35}, 9: {"align": "C", "width": 45}, 10: {"align": "C", "width": 35}, 11: {"align": "C", "width": 35}, 12: {"align": "L", "width": 38}, 13: {"align": "R", "width": 35}
# # }}







# import os
# import logging
# from openpyxl import load_workbook
# from fpdf import FPDF
# from datetime import datetime
# from customer_utils import get_customer_logo
# from PyPDF2 import PdfMerger

# # Custom PDF class for headers
# class CustomPDF(FPDF):
#     def __init__(self, customer_id, report_name, additional_header_lines, report_period, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#         self.customer_id = customer_id
#         self.report_name = report_name
#         self.additional_header_lines = additional_header_lines
#         self.report_period = report_period
#         self.header_height = 50
#         self.left_logo_path = os.path.abspath(os.path.join("static", "images", "Nextus-logo.png"))
#         self.right_logo_path = os.path.abspath(get_customer_logo(customer_id))
#         self.right_logo_path = self.right_logo_path if os.path.exists(self.right_logo_path) else os.path.abspath(
#             os.path.join("static", "images", "no_name.png"))

#     def header(self):
#         left_margin, right_margin, top_margin = self.l_margin, self.r_margin, self.t_margin
#         available_width = self.w - left_margin - right_margin
#         left_header_width = available_width // 2

#         # Header frame
#         self.rect(left_margin, top_margin, available_width, self.header_height)

#         # Left side: Report name and details
#         self.set_xy(left_margin + 2, top_margin + 2)
#         self.set_font("Arial", "B", 10)
#         self.cell(left_header_width - 4, 8, txt=self.report_name, border=0, ln=1, align='L')

#         self.set_font("Arial", size=10)
#         for line in self.additional_header_lines:
#             if line and line.strip() != self.report_period.strip():
#                 self.cell(left_header_width - 4, 6, txt=line, border=0, ln=1, align='L')

#         # Highlight report period
#         self.set_fill_color(255, 255, 0)
#         self.cell(left_header_width - 4, 6, txt=self.report_period, border=0, ln=1, align='L', fill=True)

#         # Right side: Logos and "Prepared for" text
#         self.line(left_margin + left_header_width, top_margin, left_margin + left_header_width,
#                   top_margin + self.header_height)
#         self.set_xy(left_margin + left_header_width + 2, top_margin + 2)
#         self.set_font("Arial", "B", 14)
#         self.cell(left_header_width - 4, 8, txt="Prepared for", border=0, ln=1, align='C')

#         # Insert logos
#         logo_width, logo_height, logo_padding = 50, 25, 2
#         logos_y = top_margin + 20
#         self.image(self.left_logo_path, x=left_margin + left_header_width + logo_padding, y=logos_y, w=logo_width,
#                    h=logo_height)
#         self.image(self.right_logo_path, x=left_margin + available_width - logo_width - logo_padding, y=logos_y,
#                    w=logo_width, h=logo_height)

#         self.set_y(top_margin + self.header_height + 5)


# # Function to add column headers for each page
# def add_column_headers(pdf, ws, row_number, max_col, col_width, row_heights, report_name, alignment_dict, font_size):
#     """Add column headers for each page."""
#     pdf.set_font("Arial", "B", font_size + 1)
#     for col in range(1, max_col + 1):
#         cell = ws.cell(row=row_number, column=col)
#         text = str(cell.value) if cell.value else ""
#         col_settings = alignment_dict.get(report_name, {}).get(col, {"align": "L", "width": col_width})
#         cell_align = col_settings["align"].upper()
#         cell_width = col_settings["width"]

#         while pdf.get_string_width(text + '...') > cell_width and len(text) > 0:
#             text = text[:-1]
#         if pdf.get_string_width(text) > cell_width:
#             text += "..."

#         pdf.cell(cell_width, row_heights[row_number - 1], txt=text, border=1, align=cell_align, ln=0)
#     pdf.ln(row_heights[row_number - 1])


# # 🟢 Function for AR Aging Summary (Merge Pivot Sheets)
# def convert_xlsx_to_pdf_for_ar_aging(xlsx_path, pdf_path, customer_id, font_size, report_period):
#     # Load updated alignment settings from JSON:
#     alignment_data = load_alignment_dict()

#     wb = load_workbook(xlsx_path, data_only=True)
#     all_sheets = wb.sheetnames
#     custom_width, custom_height = 297, 571
#     temp_pdf_paths = []

#     for sheet_name in all_sheets:
#         ws = wb[sheet_name]
#         max_row, max_col = ws.max_row, ws.max_column
#         report_name = ws.cell(row=1, column=1).value or "AR AGING SUMMARY"
#         additional_header_lines = [ws.cell(row=r, column=1).value for r in range(2, 5) if
#                                    ws.cell(row=r, column=1).value]

#         pdf = CustomPDF(customer_id, report_name, additional_header_lines, report_period, orientation='L', unit='mm',
#                         format=(custom_width, custom_height))
#         pdf.set_left_margin(5)
#         pdf.set_right_margin(5)
#         pdf.set_top_margin(5)
#         pdf.set_auto_page_break(auto=True, margin=10)

#         row_number = 7  # AR Aging starts from row 7
#         available_width = pdf.w - pdf.l_margin - pdf.r_margin
#         col_width = available_width / max_col
#         row_heights = [ws.row_dimensions.get(row, 10).height * 0.35 if ws.row_dimensions.get(row) else 10 for row in
#                        range(1, max_row + 1)]

#         pdf.add_page()
#         add_column_headers(pdf, ws, row_number, max_col, col_width, row_heights, report_name, alignment_data, font_size)

#         # Process table rows and add headers for new pages
#         for row in range(row_number + 1, max_row + 1):
#             if pdf.get_y() + row_heights[row - 1] > pdf.h - pdf.b_margin:
#                 pdf.add_page()
#                 add_column_headers(pdf, ws, row_number, max_col, col_width, row_heights, report_name, alignment_dict, font_size)

#             for col in range(1, max_col + 1):
#                 cell = ws.cell(row=row, column=col)
#                 text = str(cell.value) if cell.value else ""
#                 col_settings = alignment_dict.get(report_name, {}).get(col, {"align": "L", "width": col_width})
#                 cell_align = col_settings["align"].upper()
#                 cell_width = col_settings["width"]
#                 cell_height = row_heights[row - 1]

#                 if text.lower().strip() == "prepared for":
#                     continue

#                 while pdf.get_string_width(text + '...') > cell_width and len(text) > 0:
#                     text = text[:-1]
#                 if pdf.get_string_width(text) > cell_width:
#                     text += "..."

#                 pdf.set_font("Arial", "", font_size)
#                 pdf.cell(cell_width, cell_height, txt=text, border=1, align=cell_align, ln=0)

#             pdf.ln(row_heights[row - 1])

#         # Save each sheet's PDF
#         sheet_pdf_path = f"{pdf_path[:-4]}_{sheet_name}.pdf"
#         pdf.output(sheet_pdf_path)
#         temp_pdf_paths.append(sheet_pdf_path)
#         logging.info(f"PDF generated for AR Aging sheet: {sheet_name}")

#     # Merge PDFs for AR Aging Summary
#     merge_pdfs(pdf_path, temp_pdf_paths)

#     # Cleanup individual sheet PDFs after merging
#     for temp_path in temp_pdf_paths:
#         if os.path.exists(temp_path):
#             os.remove(temp_path)

#     logging.info(f"Final merged AR Aging Summary PDF saved at: {pdf_path}")


# # 🔵 Function for General Reports (Single Sheet, No Merge)
# # def convert_xlsx_to_pdf_for_general_reports(xlsx_path, pdf_path, customer_id, font_size, alignment_dict, report_period):
# #     """
# #     Generates individual PDFs for each sheet of a non-AR report using alignment settings from alignment_dict.json.
# #     """
# #     from openpyxl import load_workbook
# #     from fpdf import FPDF
# #     # Load alignment settings from JSON only.
# #     alignment_data = load_alignment_dict()

# #     wb = load_workbook(xlsx_path, data_only=True)
# #     all_sheets = wb.sheetnames
# #     custom_width, custom_height = 297, 485

# #     for sheet_name in all_sheets:
# #         ws = wb[sheet_name]
# #         max_row, max_col = ws.max_row, ws.max_column
# #         report_name = ws.cell(row=1, column=1).value or "Report"
# #         additional_header_lines = [ws.cell(row=r, column=1).value for r in range(2, 5) if ws.cell(row=r, column=1).value]

# #         pdf = CustomPDF(customer_id, report_name, additional_header_lines, report_period,
# #                         orientation='L', unit='mm', format=(custom_width, custom_height))
# #         pdf.set_left_margin(5)
# #         pdf.set_right_margin(5)
# #         pdf.set_top_margin(5)
# #         pdf.set_auto_page_break(auto=True, margin=10)

# #         row_number = 6
# #         available_width = pdf.w - pdf.l_margin - pdf.r_margin
# #         col_width = available_width / max_col
# #         row_heights = [ws.row_dimensions.get(row, 10).height * 0.35 if ws.row_dimensions.get(row) else 10 for row in range(1, max_row + 1)]

# #         pdf.add_page()
# #         # Use the alignment_data loaded from JSON.
# #         add_column_headers(pdf, ws, row_number, max_col, col_width, row_heights, report_name, alignment_data, font_size)

# #         for row in range(row_number + 1, max_row + 1):
# #             if pdf.get_y() + row_heights[row - 1] > pdf.h - pdf.b_margin:
# #                 pdf.add_page()
# #                 add_column_headers(pdf, ws, row_number, max_col, col_width, row_heights, report_name, alignment_data, font_size)

# #             for col in range(1, max_col + 1):
# #                 cell = ws.cell(row=row, column=col)
# #                 text = str(cell.value) if cell.value else ""
# #                 # Use string keys if your JSON keys are strings.
# #                 col_settings = alignment_data.get(report_name, {}).get(str(col), {"align": "L", "width": col_width})
# #                 cell_align = col_settings["align"].upper()
# #                 cell_width = col_settings["width"]
# #                 cell_height = row_heights[row - 1]

# #                 if text.lower().strip() == "prepared for":
# #                     continue

# #                 while pdf.get_string_width(text + '...') > cell_width and len(text) > 0:
# #                     text = text[:-1]
# #                 if pdf.get_string_width(text) > cell_width:
# #                     text += "..."

# #                 pdf.set_font("Arial", "", font_size)
# #                 pdf.cell(cell_width, cell_height, txt=text, border=1, align=cell_align, ln=0)
# #             pdf.ln(row_heights[row - 1])

# #         pdf.output(pdf_path)
# #         logging.info(f"PDF generated for general report: {pdf_path}")



# # Function to merge multiple PDFs into one final PDF
# def merge_pdfs(output_path, pdf_paths):
#     """Merge multiple PDFs into one final PDF."""
#     merger = PdfMerger()
#     for pdf in pdf_paths:
#         if os.path.exists(pdf):
#             merger.append(pdf)
#     merger.write(output_path)
#     merger.close()
#     logging.info(f"Merged PDF saved at: {output_path}")


# # Highlight report period in Excel
# def highlight_report_period(xlsx_path):
#     """Highlights the report period cell in yellow."""
#     from openpyxl.styles import PatternFill

#     wb = load_workbook(xlsx_path)
#     ws = wb.active
#     yellow_fill = PatternFill(start_color="FFFF00", end_color="FFFF00", fill_type="solid")
#     ws["A4"].fill = yellow_fill
#     wb.save(xlsx_path)



