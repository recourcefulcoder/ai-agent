def find_working_node(tree):
    """
        Finds the 'working' node - one containing actualsearch results.
        Rules:
        1. If 'header' (Search Results) is found outside/before 'main' -> Return 'main'.
        2. If 'header' (Search Results) is inside 'main' -> Return 'header's direct parent.
    """
    traverse_info = {
        "main_node": None,
        "target_header": None,
        "header_parent": None,
        "main_is_ancestor_of_header": False
    }
    break_recursion = False

    def traverse(node, path, parent=None):
        nonlocal break_recursion

        if not isinstance(node, dict) or break_recursion:
            return

        if node.get("role") == "main":
            traverse_info["main_node"] = node
            if traverse_info["target_header"] is not None:
                break_recursion = True
                return

        if node.get("role") == "header" and "Search Results" in node.get("name", ""):
            
            traverse_info["target_header"] = node
            traverse_info["header_parent"] = parent
            
            if traverse_info["main_node"] in path:
                traverse_info["main_is_ancestor_of_header"] = True
                break_recursion = True
                return

        children = node.get("children", [])
        if isinstance(children, list):
            for child in children:
                traverse(child, path + [node], node)
        elif isinstance(children, dict):
            for key, child in children.items():
                traverse(child, path + [node], node)

    traverse(tree, [])
    
    target_header = traverse_info["target_header"]
    main_node = traverse_info["main_node"]
    
    if not target_header:
        return main_node

    if not traverse_info["main_is_ancestor_of_header"]:
        return main_node
    else:
        return traverse_info["header_parent"]


def extract_information_blocks(working_node):
    """
    Identifies 'blocks of information' by finding links and climbing
    the tree until siblings with links are found.
    """
    parent_map = dict()
    memo_has_link = dict() # Cache results for subtree searches
    all_links = []
    blocks = []
    seen_block_ids = set()

    # --- Step 0: Decalring function to search for a link ---
    def has_link_somewhere(node) -> bool:
        node_id = id(node)
        if node_id in memo_has_link:
            return memo_has_link[node_id]
        
        # Check current node
        if isinstance(node, dict) and (node.get("role") == "link" or node.get("type") == "link"):
            memo_has_link[node_id] = True
            return True
        
        # Check children recursively
        children = node.get("children", [])
        child_list = children if isinstance(children, list) else children.values()
        
        for child in child_list:
            if isinstance(child, dict) and has_link_somewhere(child):
                memo_has_link[node_id] = True
                return True
        
        memo_has_link[node_id] = False
        return False

    # --- Step 1: Internal Helper to Map Parents & Find all Links ---
    def prepare_tree(node, parent=None):
        if not isinstance(node, dict):
            return
        
        if parent:
            parent_map[id(node)] = parent
        
        # Identify if this node is a link
        if node.get("role") == "link" or node.get("type") == "link":
            all_links.append(node)
            
        children = node.get("children", [])
        if isinstance(children, list):
            for child in children:
                prepare_tree(child, node)
        elif isinstance(children, dict):
            for key, child in children.items():
                prepare_tree(child, node)

    prepare_tree(working_node)

    # --- Step 2: Traverse up from each link ---
    for link in all_links:
        current = link
        
        while True:
            parent = parent_map.get(id(current))
            
            # Stop condition 1: We reached the working_node
            if parent is None or current == working_node:
                # The 'current' node is the block if we hit the top
                blocks.append(current)
                seen_block_ids.append(id(current))
                break
                
            # Stop condition 2: Parent has OTHER children with the "link" attribute
            siblings = parent.get("children", [])
            # Handle list vs dict of children
            sibling_list = siblings if isinstance(siblings, list) else siblings.values()
            
            has_other_link = any(
                child is not current and 
                isinstance(child, dict) and 
                (child.get("role") == "link" or child.get("type") == "link")
                for child in sibling_list
            )
            
            if has_other_link:
                # 'parent' is the "least of ancestors"
                # 'current' is the ancestor BEFORE the least of ancestors (the target)
                blocks.append(current)
                seen_block_ids.append(id(current))
                break
            
            # If parent is working_node, it acts as the LOA regardless of other links
            if parent == working_node:
                blocks.append(current)
                seen_block_ids.append(id(current))
                break
                
            # Continue climbing
            current = parent

    return blocks


def reformat_information_blocks(blocks):
    pass
