import java.io.*;

public class ResumeParser {
    public static void main(String[] args) {
        if (args.length < 1) {
            System.err.println("Usage: java ResumeParser <pdf-file-path>");
            System.exit(1);
        }

        String pdfPath = args[0];
        File file = new File(pdfPath);
        if (!file.exists()) {
            System.err.println("Error: File does not exist: " + pdfPath);
            System.exit(2);
        }

        try {
            // Read first few bytes to verify it's a PDF
            byte[] header = new byte[8];
            try (FileInputStream fis = new FileInputStream(file)) {
                int read = fis.read(header);
                if (read < 4) {
                    System.err.println("Error: File is too small to be a PDF.");
                    System.exit(3);
                }
            }

            String headerStr = new String(header);
            boolean isPDF = headerStr.startsWith("%PDF");
            
            long fileSize = file.length();
            String fileName = file.getName();
            
            // Print formatted JSON metadata to stdout for Python subprocess exchange
            System.out.println("{");
            System.out.println("  \"file_name\": \"" + fileName + "\",");
            System.out.println("  \"file_size_bytes\": " + fileSize + ",");
            System.out.println("  \"is_valid_pdf\": " + isPDF + ",");
            System.out.println("  \"parser_backend\": \"Java JDK\",");
            System.out.println("  \"status\": \"success\"");
            System.out.println("}");
            
        } catch (Exception e) {
            System.err.println("Error reading file: " + e.getMessage());
            System.exit(4);
        }
    }
}
