enum FsNodeType { folder, file }

class FsNode {
  final String? id;
  final FsNodeType type;
  final String name;
  final String path;
  final String parentPath;
  final String? content;
  final int sortOrder;
  final DateTime? createdAt;
  final DateTime? updatedAt;

  // For tree structure (mutable for UI state)
  List<FsNode> children;
  bool isExpanded;
  bool isLoading;

  FsNode({
    this.id,
    required this.type,
    required this.name,
    required this.path,
    required this.parentPath,
    this.content,
    this.sortOrder = 0,
    this.createdAt,
    this.updatedAt,
    List<FsNode>? children,
    this.isExpanded = false,
    this.isLoading = false,
  }) : children = children ?? [];

  bool get isFolder => type == FsNodeType.folder;
  bool get isFile => type == FsNodeType.file;

  String get extension {
    if (!name.contains('.')) return '';
    return name.split('.').last.toLowerCase();
  }

  bool get isMarkdown => extension == 'md';

  factory FsNode.fromJson(Map<String, dynamic> json) {
    return FsNode(
      id: json['id'] as String?,
      type: json['type'] == 'folder' ? FsNodeType.folder : FsNodeType.file,
      name: json['name'] ?? '',
      path: json['path'] ?? '',
      parentPath: json['parent_path'] ?? '/',
      content: json['content'] as String?,
      sortOrder: (json['sort_order'] ?? 0).toInt(),
      createdAt: json['created_at'] != null && json['created_at'] != ''
          ? DateTime.parse(json['created_at']).toLocal()
          : null,
      updatedAt: json['updated_at'] != null && json['updated_at'] != ''
          ? DateTime.parse(json['updated_at']).toLocal()
          : null,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      if (id != null) 'id': id,
      'type': type == FsNodeType.folder ? 'folder' : 'file',
      'name': name,
      'path': path,
      'parent_path': parentPath,
      if (content != null) 'content': content,
      'sort_order': sortOrder,
    };
  }

  Map<String, dynamic> toCreateJson() {
    return {
      'type': type == FsNodeType.folder ? 'folder' : 'file',
      'name': name,
      'parent_path': parentPath,
      if (content != null) 'content': content,
      'sort_order': sortOrder,
    };
  }

  FsNode copyWith({
    String? id,
    FsNodeType? type,
    String? name,
    String? path,
    String? parentPath,
    String? content,
    int? sortOrder,
    DateTime? createdAt,
    DateTime? updatedAt,
    List<FsNode>? children,
    bool? isExpanded,
    bool? isLoading,
  }) {
    return FsNode(
      id: id ?? this.id,
      type: type ?? this.type,
      name: name ?? this.name,
      path: path ?? this.path,
      parentPath: parentPath ?? this.parentPath,
      content: content ?? this.content,
      sortOrder: sortOrder ?? this.sortOrder,
      createdAt: createdAt ?? this.createdAt,
      updatedAt: updatedAt ?? this.updatedAt,
      children: children ?? this.children,
      isExpanded: isExpanded ?? this.isExpanded,
      isLoading: isLoading ?? this.isLoading,
    );
  }

  // Create a new folder node
  factory FsNode.folder({
    required String name,
    required String parentPath,
    int sortOrder = 0,
  }) {
    return FsNode(
      type: FsNodeType.folder,
      name: name,
      path: parentPath == '/' ? '/$name' : '$parentPath/$name',
      parentPath: parentPath,
      sortOrder: sortOrder,
    );
  }

  // Create a new file node
  factory FsNode.file({
    required String name,
    required String parentPath,
    String? content,
    int sortOrder = 0,
  }) {
    return FsNode(
      type: FsNodeType.file,
      name: name,
      path: parentPath == '/' ? '/$name' : '$parentPath/$name',
      parentPath: parentPath,
      content: content,
      sortOrder: sortOrder,
    );
  }
}
