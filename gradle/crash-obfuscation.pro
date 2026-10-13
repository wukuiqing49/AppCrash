# 宿主应用显式加载，不能作为库的 consumer rules 自动传播。
# 全局选项：会重打包宿主内所有允许重命名的类，不限于 lib_crash。
-repackageclasses 'o'

# 原始源码文件名不出现在未经还原的堆栈中，保留行号供 mapping 还原。
-renamesourcefileattribute SourceFile
-keepattributes SourceFile,LineNumberTable

# 不添加 -keep class com.wkq.crash.**，否则会阻止库名称混淆。
